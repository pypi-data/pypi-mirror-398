# src/apathetic_logging/logger.py
"""Core Logger implementation for Apathetic Logging.

See https://docs.python.org/3/library/logging.html#logging.Logger for the
complete list of standard library Logger methods that are extended by this class.

Docstrings are adapted from the standard library logging.Logger documentation
licensed under the Python Software Foundation License Version 2.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, TextIO, cast

from .constants import (
    ApatheticLogging_Internal_Constants,
)
from .dual_stream_handler import (
    ApatheticLogging_Internal_DualStreamHandler,
)
from .registry_data import (
    ApatheticLogging_Internal_RegistryData,
)
from .safe_logging import (
    ApatheticLogging_Internal_SafeLogging,
)
from .tag_formatter import (
    ApatheticLogging_Internal_TagFormatter,
)


class ApatheticLogging_Internal_LoggerCore(logging.Logger):  # noqa: N801  # pyright: ignore[reportUnusedClass]
    """Core Logger implementation for all Apathetic tools.

    This class contains the core Logger implementation.
    It provides all the custom methods and functionality for apathetic logging.
    """

    enable_color: bool = False
    """Enable ANSI color output for log messages."""

    _logging_module_extended: bool = False

    # if stdout or stderr are redirected, we need to repoint
    _last_stream_ids: tuple[TextIO, TextIO] | None = None

    DEFAULT_STACKLEVEL = 2
    """Default stacklevel for errorIfNotDebug/criticalIfNotDebug methods."""

    def __init__(
        self,
        name: str,
        level: int | None = ApatheticLogging_Internal_Constants.INHERIT_LEVEL,
        *,
        enable_color: bool | None = None,
        propagate: bool | None = None,
    ) -> None:
        """Initialize the logger.

        Sets up color support and log propagation. Loggers default to INHERIT_LEVEL
        (i.e. NOTSET) to inherit level from root logger. Defaults to propagate=True for
        root logger architecture.

        **Contract with getLoggerOfType():** The propagate setting follows a two-phase
        initialization pattern when propagate=None:
        1. __init__ sets _propagate_explicit=False to indicate the value was not
           explicitly provided by the user.
        2. After logger creation, getLoggerOfType() calls _applyPropagateSetting(),
           which checks _propagate_explicit and applies the registry or default value.
        This allows explicit user overrides (propagate=True/False in __init__) to take
        precedence over registry/default values set later via _applyPropagateSetting().

        Args:
            name: Logger name
            level: Initial logging level. If None, auto-resolves via
                determineLogLevel(). If INHERIT_LEVEL (i.e. NOTSET)
                (default), inherits from root logger. Otherwise, sets
                explicit level.
            enable_color: Force color output on/off, or None for auto-detect
            propagate: Propagate setting. If None, uses registered setting or
                defaults to True. If True, messages propagate to parent loggers.

        """
        # it is too late to call extendLoggingModule

        _constants = ApatheticLogging_Internal_Constants
        super().__init__(name, _constants.INHERIT_LEVEL if level is None else level)

        # Handle None level - auto-resolve via determineLogLevel
        if level is None:
            # Initialize with INHERIT_LEVEL (i.e. NOTSET) first, then resolve
            self.setLevel(self.determineLogLevel())

        # detect color support once per instance
        self.enable_color = (
            enable_color
            if enable_color is not None
            else type(self).determineColorEnabled()
        )

        # Set propagate - use provided value, or will be set by _applyPropagateSetting
        if propagate is not None:
            self.setPropagate(propagate)
        else:
            self._propagate_explicit = False  # Will be set by _applyPropagateSetting

        # handler attachment will happen in _log() with manageHandlers()

    def manageHandlers(self, *, manage_handlers: bool | None = None) -> None:
        """Manage apathetic handlers for this logger.

        Root logger always gets an apathetic handler. Child loggers only get
        apathetic handlers if they're not propagating (propagate=False),
        otherwise they rely on root logger's handler via propagation.

        Only manages DualStreamHandler instances. User-added handlers are
        left untouched.

        Rebuilds handlers if they're missing or if stdout/stderr have changed.

        Args:
            manage_handlers: If True, manage handlers (even in compat mode).
                If None, checks compatibility mode: in compat mode, handlers are
                not managed unless explicitly enabled. If False, returns early
                without managing handlers. Defaults to None.

        """
        _constants = ApatheticLogging_Internal_Constants

        # Resolve manage_handlers parameter
        if manage_handlers is None:
            # Check compatibility mode - in compat mode, don't manage handlers
            # unless explicitly requested
            from .logging_utils import (  # noqa: PLC0415
                ApatheticLogging_Internal_LoggingUtils,
            )

            _logging_utils = ApatheticLogging_Internal_LoggingUtils
            compat_mode = _logging_utils._getCompatibilityMode()  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

            if compat_mode:
                # In compat mode, don't manage handlers by default
                return

            # Not in compat mode, use default from constants
            manage_handlers = _constants.DEFAULT_MANAGE_HANDLERS

        # Return early if management is disabled
        if not manage_handlers:
            return

        _dual_stream_handler = ApatheticLogging_Internal_DualStreamHandler
        _tag_formatter = ApatheticLogging_Internal_TagFormatter
        _safe_logging = ApatheticLogging_Internal_SafeLogging

        # Identify apathetic handlers
        apathetic_handlers = [
            h
            for h in self.handlers
            if isinstance(h, _dual_stream_handler.DualStreamHandler)
        ]

        # Propagating child loggers should not have apathetic handlers
        # Only remove handlers if we previously managed them (indicated by
        # _last_stream_ids being set), to avoid removing manually-added handlers
        # Root logger can have name "" (ROOT_LOGGER_KEY) or "root" (ROOT_LOGGER_NAME)
        is_root = self.name in {
            _constants.ROOT_LOGGER_KEY,
            _constants.ROOT_LOGGER_NAME,
        }
        if not is_root and self.propagate:
            # Only remove apathetic handlers if we previously managed them
            # (indicated by _last_stream_ids being set)
            if self._last_stream_ids is not None and apathetic_handlers:
                # We previously managed handlers for this logger, remove them
                for handler in apathetic_handlers:
                    self.removeHandler(handler)
            return

        # Root logger or non-propagating child logger - ensure it has an
        # apathetic handler. Check if rebuild is needed (missing handler or
        # streams changed)
        needs_rebuild = False
        if not apathetic_handlers:
            needs_rebuild = True
        elif self._last_stream_ids is not None:
            last_stdout, last_stderr = self._last_stream_ids
            if last_stdout is not sys.stdout or last_stderr is not sys.stderr:
                needs_rebuild = True
        else:
            # _last_stream_ids is None but we have handlers - rebuild to set it
            needs_rebuild = True

        if needs_rebuild:
            # Remove existing apathetic handlers (there should only be one, but be safe)
            for handler in apathetic_handlers:
                self.removeHandler(handler)

            # Add new apathetic handler
            h = _dual_stream_handler.DualStreamHandler()
            h.setFormatter(_tag_formatter.TagFormatter("%(message)s"))
            h.enable_color = self.enable_color
            self.addHandler(h)
            self._last_stream_ids = (sys.stdout, sys.stderr)
            _safe_logging.safeTrace(
                "manageHandlers()",
                f"rebuilt_handlers={self.handlers}",
            )

    def _log(  # type: ignore[override]
        self,
        level: int,
        msg: str,
        args: tuple[Any, ...],
        **kwargs: Any,
    ) -> None:
        """Log a message with the specified level.

        Changed:
        - Automatically manages handlers via manageHandlers()

        Args:
            level: The numeric logging level
            msg: The message format string
            args: Arguments for the message format string
            **kwargs: Additional keyword arguments passed to the base implementation

        Wrapper for logging.Logger._log.

        https://docs.python.org/3.10/library/logging.html#logging.Logger._log

        """
        self.manageHandlers()
        super()._log(level, msg, args, **kwargs)

    def setLevel(
        self,
        level: int | str,
        *,
        minimum: bool | None = False,
    ) -> None:
        """Set the logging level of this logger.

        Changed:
        - Accepts both int and str level values (case-insensitive for strings)
        - Automatically resolves string level names to numeric values
        - Supports custom level names (TEST, TRACE, BRIEF, DETAIL, SILENT)
        - Validates that custom levels are registered properly (no duplicate
          numeric level values via addLevelName)
        - In compatibility mode, accepts any level value (including 0 and negative)
          matching stdlib behavior.
        - Added `minimum` parameter: if True, only sets the level if it's more
          verbose (lower numeric value) than the current level

        Args:
            level: The logging level, either as an integer or a string name
                (case-insensitive). Standard levels (DEBUG, INFO, WARNING, ERROR,
                CRITICAL) and custom levels (TEST, TRACE, BRIEF, DETAIL, SILENT)
                are supported. Use 0/NOTSET to inherit level from parent logger.
            minimum: If True, only set the level if it's more verbose (lower
                numeric value) than the current level. This prevents downgrading
                from a more verbose level (e.g., TRACE) to a less verbose one
                (e.g., DEBUG). Defaults to False. None is accepted and treated
                as False.

        Wrapper for logging.Logger.setLevel.

        https://docs.python.org/3.10/library/logging.html#logging.Logger.setLevel

        """
        from .logging_utils import (  # noqa: PLC0415
            ApatheticLogging_Internal_LoggingUtils,
        )

        _logging_utils = ApatheticLogging_Internal_LoggingUtils
        _constants = ApatheticLogging_Internal_Constants

        # Resolve string to integer if needed using utility function
        level_name: str | None = None
        if isinstance(level, str):
            level_name = level
            level = _logging_utils.getLevelNumber(level)

        # Handle minimum level logic (None is treated as False)
        if minimum:
            current_level = self.getEffectiveLevel()
            # Lower number = more verbose, so only set if new level is more verbose
            if level >= current_level:
                # Don't downgrade - keep current level
                return

        # Validate level only if it's <= 0 in improved mode
        # (validate that custom negative levels are not used)
        self.validateLevel(level, level_name=level_name)

        super().setLevel(level)
        # Clear the isEnabledFor cache when level changes, as cached values
        # may be stale (e.g., if level was TRACE and cached isEnabledFor(TRACE)=True,
        # then changing to DEBUG should invalidate that cache entry)
        if hasattr(self, "_cache"):
            self._cache.clear()  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]

    def setLevelMinimum(self, level: int | str) -> None:
        """Set the logging level only if it's more verbose than the current level.

        This convenience method is equivalent to calling
        ``setLevel(level, minimum=True)``. It prevents downgrading from a more
        verbose level (e.g., TRACE) to a less verbose one (e.g., DEBUG).

        Args:
            level: The logging level, either as an integer or a string name
                (case-insensitive). Standard levels (DEBUG, INFO, WARNING, ERROR,
                CRITICAL) and custom levels (TEST, TRACE, BRIEF, DETAIL, SILENT)
                are supported.

        Example:
            >>> logger = getLogger("mymodule")
            >>> logger.setLevel("TRACE")
            >>> # This won't downgrade from TRACE to DEBUG
            >>> logger.setLevelMinimum("DEBUG")
            >>> assert logger.levelName == "TRACE"  # Still TRACE
            >>> # This will upgrade from INFO to DEBUG
            >>> logger.setLevel("INFO")
            >>> logger.setLevelMinimum("DEBUG")
            >>> assert logger.levelName == "DEBUG"  # Upgraded to DEBUG

        """
        self.setLevel(level, minimum=True)

    def setLevelInherit(self) -> None:
        """Set the logger to inherit its level from the parent logger.

        This convenience method is equivalent to calling ``setLevel(0)`` or
        ``setLevel(INHERIT_LEVEL)`` or ``setLevel("NOTSET")``. It explicitly
        sets the logger to INHERIT_LEVEL (i.e. NOTSET) so it inherits its
        effective level from the root logger or parent logger.

        Example:
            >>> logger = getLogger("mymodule")
            >>> logger.setLevel("DEBUG")
            >>> # Set to inherit from root logger
            >>> logger.setLevelInherit()
            >>> assert logger.levelName == "NOTSET"
            >>> assert logger.effectiveLevel == root.level  # Inherits from root

        """
        _constants = ApatheticLogging_Internal_Constants
        self.setLevel(_constants.INHERIT_LEVEL)

    def setPropagate(
        self,
        propagate: bool,  # noqa: FBT001
        *,
        manage_handlers: bool | None = None,
    ) -> None:
        """Set the propagate setting for this logger.

        When propagate is True, messages are passed to handlers of higher level
        (ancestor) loggers, in addition to any handlers attached to this logger.
        When False, messages are not passed to handlers of ancestor loggers.

        Args:
            propagate: If True, messages propagate to parent loggers. If False,
                messages only go to this logger's handlers.
            manage_handlers: If True, automatically manage apathetic handlers
                based on propagate setting. If None, uses DEFAULT_MANAGE_HANDLERS
                from constants. If False, only sets propagate without managing handlers.
                In compat_mode, this may default to False.

        Wrapper for logging.Logger.propagate attribute.

        https://docs.python.org/3.10/library/logging.html#logging.Logger.propagate

        """
        self.propagate = propagate
        self._propagate_explicit = True  # Mark as explicitly set

        # Always call manageHandlers - it will handle the manage_handlers parameter
        self.manageHandlers(manage_handlers=manage_handlers)

    def setLevelAndPropagate(
        self,
        level: int | str,
        *,
        minimum: bool | None = False,
        manage_handlers: bool | None = None,
    ) -> None:
        """Set the logging level and propagate setting together in a smart way.

        This convenience method combines setLevel() and setPropagate() with
        intelligent defaults:
        - If level is INHERIT_LEVEL (NOTSET): sets propagate=True
        - If level is a specific level: sets propagate=False
        - On root logger: only sets level (propagate is unchanged)

        This matches common use cases: when inheriting level, you typically
        want to propagate to parent handlers. When setting an explicit level,
        you typically want isolated logging with your own handler.

        Args:
            level: The logging level, either as an integer or a string name
                (case-insensitive). Standard levels (DEBUG, INFO, WARNING, ERROR,
                CRITICAL) and custom levels (TEST, TRACE, BRIEF, DETAIL, SILENT)
                are supported. Use INHERIT_LEVEL (0) or "NOTSET" to inherit.
            minimum: If True, only set the level if it's more verbose (lower
                numeric value) than the current level. This prevents downgrading
                from a more verbose level (e.g., TRACE) to a less verbose one
                (e.g., DEBUG). Defaults to False. None is accepted and treated
                as False.
            manage_handlers: If True, automatically manage apathetic handlers
                based on propagate setting. If None, uses DEFAULT_MANAGE_HANDLERS
                from constants. If False, only sets propagate without managing handlers.
                In compat_mode, this may default to False.

        Example:
            >>> logger = getLogger("mymodule")
            >>> # Set to inherit level and propagate to root
            >>> logger.setLevelAndPropagate(INHERIT_LEVEL)
            >>> # Set explicit level and disable propagation (isolated logging)
            >>> logger.setLevelAndPropagate("debug")

        """
        from .logging_utils import (  # noqa: PLC0415
            ApatheticLogging_Internal_LoggingUtils,
        )

        _logging_utils = ApatheticLogging_Internal_LoggingUtils
        _constants = ApatheticLogging_Internal_Constants

        # Resolve string to integer if needed using utility function
        if isinstance(level, str):
            level_int = _logging_utils.getLevelNumber(level)
        else:
            level_int = level

        # Set the level first
        self.setLevel(level_int, minimum=minimum)

        # Determine propagate setting based on level
        # Only set propagate if not root logger
        # Root logger can have name "" (ROOT_LOGGER_KEY) or "root" (ROOT_LOGGER_NAME)
        is_root = self.name in {
            _constants.ROOT_LOGGER_KEY,
            _constants.ROOT_LOGGER_NAME,
        }
        if not is_root:
            if level_int == _constants.INHERIT_LEVEL:
                # INHERIT_LEVEL -> propagate=True
                self.setPropagate(True, manage_handlers=manage_handlers)
            else:
                # Specific level -> propagate=False
                self.setPropagate(False, manage_handlers=manage_handlers)
        # Root logger: propagate is unchanged (root always has handlers)

    @classmethod
    def determineColorEnabled(cls) -> bool:
        """Return True if colored output should be enabled."""
        # Respect explicit overrides
        if "NO_COLOR" in os.environ:
            return False
        if os.getenv("FORCE_COLOR", "").lower() in {"1", "true", "yes"}:
            return True

        # Auto-detect: use color if output is a TTY
        return sys.stdout.isatty()

    @staticmethod
    def validateLevel(
        level: int,
        *,
        level_name: str | None = None,
    ) -> None:
        """Validate that a level value is not negative (>= 0).

        Custom levels with values < 0 (negative) are discouraged by PEP 282.
        Level 0 (NOTSET/INHERIT_LEVEL) is allowed - it causes loggers to
        inherit from parent loggers. For custom levels to not be confusing,
        duplicate numeric values are prevented via addLevelName() validation.

        In compatibility mode, validation is skipped (all levels are accepted).

        Args:
            level: The numeric level value to validate
            level_name: Optional name for the level (for error messages).
                If None, will attempt to get from getLevelName()

        Raises:
            ValueError: If level < 0 (negative levels are discouraged)

        Example:
            >>> Logger.validateLevel(5, level_name="TRACE")
            >>> Logger.validateLevel(0, level_name="NOTSET")  # OK - allows inheritance
            >>> Logger.validateLevel(-5, level_name="NEGATIVE")
            ValueError: Level 'NEGATIVE' has value -5, which is < 0...

        """
        from .logging_utils import (  # noqa: PLC0415
            ApatheticLogging_Internal_LoggingUtils,
        )

        _logging_utils = ApatheticLogging_Internal_LoggingUtils
        _constants = ApatheticLogging_Internal_Constants

        # Check compatibility mode
        compat_mode = _logging_utils._getCompatibilityMode()  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

        if compat_mode:
            return

        if level < _constants.INHERIT_LEVEL:
            if level_name is None:
                level_name = _logging_utils.getLevelNameStr(level)
            msg = (
                f"Level '{level_name}' has value {level}, "
                "which is < 0. This is discouraged by PEP 282 and"
                " results can lead to unexpected behavior."
            )
            raise ValueError(msg)

    @staticmethod
    def addLevelName(level: int, level_name: str) -> None:
        """Associate a level name with a numeric level.

        Changed:
        - Validates that level is not negative (>= 0) to prevent issues per PEP 282
        - Checks for duplicate numeric level values to prevent confusion
        - Sets logging.<LEVEL_NAME> attribute for convenience, matching the
          pattern of built-in levels (logging.DEBUG, logging.INFO, etc.)
        - Sets apathetic_logging.<LEVEL_NAME>_LEVEL attribute for consistency
          with constant naming pattern (e.g., apathetic_logging.TRACE_LEVEL,
          apathetic_logging.CUSTOM_LEVEL)
        - Validates existing attributes to ensure consistency

        Args:
            level: The numeric level value (must be >= 0 and not already used
                by another level name to avoid confusion)
            level_name: The name to associate with this level

        Raises:
            ValueError: If level < 0 (negative levels are discouraged by PEP 282)
            ValueError: If a different level name already has this numeric value
            ValueError: If logging.<LEVEL_NAME> already exists with a different value
            ValueError: If apathetic_logging.<LEVEL_NAME>_LEVEL already exists
                with a different value

        Wrapper for logging.addLevelName.

        https://docs.python.org/3.10/library/logging.html#logging.addLevelName

        """
        # Validate level is not negative
        ApatheticLogging_Internal_LoggerCore.validateLevel(level, level_name=level_name)

        # Check for duplicate numeric level values
        # Get the existing name for this level value
        existing_name = logging.getLevelName(level)
        # Check if this level value is already registered to a different name
        # (getLevelName returns "Level {n}" format for unknown levels)
        if not existing_name.startswith("Level ") and existing_name != level_name:
            msg = (
                f"Level value {level} is already registered as '{existing_name}'. "
                f"Cannot register as '{level_name}'. "
                "Each level value must have a unique name to avoid confusion."
            )
            raise ValueError(msg)

        # Check if attribute already exists in logging namespace and validate it
        existing_value = getattr(logging, level_name, None)
        if existing_value is not None:
            # If it exists, it must be a valid level value (positive integer)
            if not isinstance(existing_value, int):
                msg = (
                    f"Cannot set logging.{level_name}: attribute already exists "
                    f"with non-integer value {existing_value!r}. "
                    "Level attributes must be integers."
                )
                raise ValueError(msg)
            # Validate existing value is positive
            ApatheticLogging_Internal_LoggerCore.validateLevel(
                existing_value,
                level_name=level_name,
            )
            if existing_value != level:
                msg = (
                    f"Cannot set logging.{level_name}: attribute already exists "
                    f"with different value {existing_value} "
                    f"(trying to set {level}). "
                    "Level attributes must match the level value."
                )
                raise ValueError(msg)
            # If it exists and matches, we can proceed (idempotent)

        # Get apathetic_logging namespace class
        namespace_module = sys.modules.get("apathetic_logging")
        namespace_class = None
        if namespace_module is not None:
            namespace_class = getattr(namespace_module, "apathetic_logging", None)

        # Use _LEVEL suffix for apathetic_logging namespace to match constant pattern
        # (e.g., apathetic_logging.TRACE_LEVEL instead of apathetic_logging.TRACE)
        apathetic_level_name = f"{level_name}_LEVEL"

        # Check if attribute already exists in apathetic_logging namespace
        # and validate it
        if namespace_class is not None:
            existing_apathetic_value = getattr(
                namespace_class,
                apathetic_level_name,
                None,
            )
            if existing_apathetic_value is not None:
                # If it exists, it must be a valid level value (positive integer)
                if not isinstance(existing_apathetic_value, int):
                    msg = (
                        f"Cannot set apathetic_logging.{apathetic_level_name}: "
                        f"attribute already exists with non-integer value "
                        f"{existing_apathetic_value!r}. "
                        "Level attributes must be integers."
                    )
                    raise ValueError(msg)
                # Validate existing value is positive
                ApatheticLogging_Internal_LoggerCore.validateLevel(
                    existing_apathetic_value,
                    level_name=level_name,
                )
                if existing_apathetic_value != level:
                    msg = (
                        f"Cannot set apathetic_logging.{apathetic_level_name}: "
                        f"attribute already exists with different value "
                        f"{existing_apathetic_value} (trying to set {level}). "
                        "Level attributes must match the level value."
                    )
                    raise ValueError(msg)
                # If it exists and matches, we can proceed (idempotent)

        logging.addLevelName(level, level_name)
        # Set convenience attribute matching built-in levels (logging.DEBUG, etc.)
        setattr(logging, level_name, level)

        # Set convenience attribute on apathetic_logging namespace class
        # with _LEVEL suffix to match constant pattern
        # (e.g., apathetic_logging.TRACE_LEVEL, apathetic_logging.CUSTOM_LEVEL)
        if namespace_class is not None:
            setattr(namespace_class, apathetic_level_name, level)

    @classmethod
    def extendLoggingModule(
        cls,
        *,
        replace_root: bool | None = None,
        port_handlers: bool | None = None,
        port_level: bool | None = None,
    ) -> bool:
        """The return value tells you if we ran or not.
        If it is False and you're calling it via super(),
        you can likely skip your code too.

        Args:
            replace_root: Whether to replace the root logger if it's not the correct
                type. If None (default), checks the registry setting (set via
                registerReplaceRootLogger()). If not set in registry, defaults to True
                for backward compatibility. When False, the root logger will not be
                replaced, allowing applications to use their own custom logger class
                for the root logger.
            port_handlers: Whether to port handlers from the old root logger to the
                new logger. If None (default), checks the registry setting (set via
                registerPortHandlers()). If not set in registry, defaults to True
                (DEFAULT_PORT_HANDLERS from constants.py). When False, the new
                logger manages its own handlers via manageHandlers().
            port_level: Whether to port level from the old root logger to the new
                logger. If None (default), checks the registry setting (set via
                registerPortLevel()). If not set in registry, defaults to True
                (DEFAULT_PORT_LEVEL from constants.py). When False, the new root
                logger uses determineLogLevel() to get a sensible default. When
                True, the old level is preserved.

        Note for tests:
            When testing isinstance checks on logger instances, use
            ``logging.getLoggerClass()`` instead of direct class references
            (e.g., ``mod_alogs.Logger``). This works reliably in both package
            and stitched runtime modes because it uses the actual class object
            that was set via ``logging.setLoggerClass()``, rather than a class
            reference from the import shim which may have different object identity
            in stitched mode.

        Example:
                # ✅ Good: Works in both package and stitched modes
                assert isinstance(logger, logging.getLoggerClass())

                # ❌ May fail in stitched mode due to class identity differences
                assert isinstance(logger, mod_alogs.Logger)

        """
        _constants = ApatheticLogging_Internal_Constants
        # Check if this specific class has already extended the module
        # (not inherited from base class)
        already_extended = getattr(cls, "_logging_module_extended", False)

        # Always set the logger class to cls, even if already extended.
        # This allows subclasses to override the logger class.
        # stdlib unwrapped
        logging.setLoggerClass(cls)

        # Check if root logger exists and needs to be replaced
        # This handles the case where root logger was created before
        # extendLoggingModule() was called (e.g., if stdlib logging was imported first)
        # We always check if root logger needs replacement (even if already_extended),
        # but only replace on first call OR if root logger is wrong type
        # Determine if we should replace the root logger
        # Check parameter first, then registry, then default from constants
        if replace_root is None:
            from .registry_data import (  # noqa: PLC0415
                ApatheticLogging_Internal_RegistryData,
            )

            _registry_data = ApatheticLogging_Internal_RegistryData
            _registered_replace_root = (
                _registry_data.registered_internal_replace_root_logger
            )
            replace_root = (
                _registered_replace_root
                if _registered_replace_root is not None
                else _constants.DEFAULT_REPLACE_ROOT_LOGGER
            )

        # Check if user has explicitly configured the root logger via
        # ensureRootLogger(). If they have, respect their choice and don't touch it.
        # Use the main apathetic_logging module, not the logger submodule
        # (important for stitched mode where there's only one module)
        namespace_module = sys.modules.get("apathetic_logging")
        user_configured_root = getattr(
            namespace_module, "_root_logger_user_configured", False
        )

        # Get root logger directly (logging.root or from registry)
        root_logger = logging.getLogger(_constants.ROOT_LOGGER_KEY)

        # Determine if we should replace the root logger
        # Only replace if:
        # 1. replace_root is True (parameter, registry, or default)
        # 2. User has NOT explicitly configured root via ensureRootLogger()
        # 3. Either on first call (not already_extended) OR root logger is wrong type
        #
        # This replaces stdlib loggers (including subclasses like RootLogger)
        # while respecting user configuration.
        should_replace_root = (
            replace_root
            and not user_configured_root
            and (not already_extended or not isinstance(root_logger, cls))
        )
        if should_replace_root:
            # Root logger is wrong type - need to replace it
            # Remove old root logger from registry
            from .logging_utils import (  # noqa: PLC0415
                ApatheticLogging_Internal_LoggingUtils,
            )

            _logging_utils = ApatheticLogging_Internal_LoggingUtils

            # Remove from registry
            _logging_utils.removeLogger(_constants.ROOT_LOGGER_KEY)

            # Clear logging.root (root logger is stored there as a module-level
            # variable). This is necessary because logging.getLogger("") returns
            # logging.root directly.
            if hasattr(logging, "root"):
                logging.root = None  # type: ignore[assignment]

            # Create new root logger using the manager's getLogger method
            # The logger class is already set to cls (line 687), so this will create
            # a logger of type cls. We use the manager directly because it handles
            # root logger creation properly even when logging.root is None.
            # Note: We don't use _getOrCreateLoggerOfType() here because:
            # 1. It would call _setLoggerClassTemporarily() which is unnecessary
            #    since we've already set the logger class to cls
            # 2. The manager's getLogger() is the most direct way to create a root
            #    logger
            # 3. This avoids any potential issues with logging.root being None
            new_root_logger = logging.Logger.manager.getLogger(
                _constants.ROOT_LOGGER_KEY
            )

            # Ensure root logger has correct name ("root" not "")
            # Python's logging module sets root logger name to "root" even though
            # it's retrieved with "". We need to ensure our replacement maintains
            # this behavior.
            if new_root_logger.name != _constants.ROOT_LOGGER_NAME:
                new_root_logger.name = _constants.ROOT_LOGGER_NAME

            # Update logging.root to point to the new root logger
            # This is necessary because logging.getLogger("") returns logging.root
            # directly, and we want to ensure it points to our new logger instance.
            if hasattr(logging, "root"):
                logging.root = new_root_logger  # type: ignore[assignment]

            # Also update logging.Logger.manager.root to point to new root logger
            # The manager's root must stay in sync with logging.root, otherwise
            # they reference different objects and child loggers may have incorrect
            # parent references.
            logging.Logger.manager.root = new_root_logger  # type: ignore[assignment]

            # Port state from old root logger to new root logger
            # (also reconnects child loggers internally)
            _logging_utils.portLoggerState(
                root_logger,
                new_root_logger,
                port_handlers=port_handlers,
                port_level=port_level,
            )

        # If already extended, skip the rest (level registration, etc.)
        if already_extended:
            return False
        cls._logging_module_extended = True

        # Sanity check: validate TAG_STYLES keys are in LEVEL_ORDER
        if __debug__:
            _tag_levels = set(_constants.TAG_STYLES.keys())
            _known_levels = {lvl.upper() for lvl in _constants.LEVEL_ORDER}
            if not _tag_levels <= _known_levels:
                _msg = "TAG_STYLES contains unknown levels"
                raise AssertionError(_msg)

        # Register custom levels with validation
        # addLevelName() also sets logging.TEST, logging.TRACE, etc. attributes
        cls.addLevelName(_constants.TEST_LEVEL, "TEST")
        cls.addLevelName(_constants.TRACE_LEVEL, "TRACE")
        cls.addLevelName(_constants.DETAIL_LEVEL, "DETAIL")
        cls.addLevelName(_constants.BRIEF_LEVEL, "BRIEF")
        cls.addLevelName(_constants.SILENT_LEVEL, "SILENT")

        return True

    @classmethod
    def ensureRootLogger(
        cls,
        *,
        logger_class: type[logging.Logger] | None = None,
        always_replace: bool = False,
        accept_subclass: bool = True,
    ) -> None:
        """Ensure the root logger is of the specified type.

        This function allows applications to explicitly set what the root logger
        should be. After calling this function, the root logger will not be
        replaced by subsequent calls to extendLoggingModule().

        Args:
            logger_class: The desired logger class for the root logger. If None
                (default), uses the current default logger class
                (logging.getLoggerClass()). If specified, the root logger will be
                created/replaced to be an instance of this class.
            always_replace: If True, always replace the root logger even if it's
                already the correct type or a subclass. If False (default), respects
                existing root logger if it's already the desired type or a subclass
                (when accept_subclass=True). This parameter is mainly for forcing
                a fresh creation of the root logger.
            accept_subclass: If True (default), considers a root logger that is a
                subclass of `logger_class` as acceptable (no replacement needed).
                If False, only exact type match is considered acceptable. This
                affects the behavior when always_replace=False.

        Example:
            # Ensure root logger is the default apathetic logger
            apathetic_logging.Logger.ensureRootLogger()

            # Ensure root logger is a custom logger class
            class MyLogger(apathetic_logging.Logger):
                pass

            apathetic_logging.Logger.ensureRootLogger(logger_class=MyLogger)

        Note:
            This function sets a module-level flag indicating the user has
            explicitly configured the root logger. Subsequent calls to
            extendLoggingModule() will respect this and not attempt to replace
            the root logger.
        """
        _constants = ApatheticLogging_Internal_Constants

        # If logger_class is None, use the current default logger class
        if logger_class is None:
            logger_class = logging.getLoggerClass()

        # Get current root logger
        root_logger = logging.getLogger(_constants.ROOT_LOGGER_KEY)

        # Determine if we should replace
        should_replace = always_replace
        if not should_replace:
            # Smart mode: only replace if root is not the desired type
            if accept_subclass:
                # Accept exact match or subclass
                should_replace = not isinstance(root_logger, logger_class)
            else:
                # Require exact match
                should_replace = type(root_logger) is not logger_class

        if should_replace:
            from .logging_utils import (  # noqa: PLC0415
                ApatheticLogging_Internal_LoggingUtils,
            )

            _logging_utils = ApatheticLogging_Internal_LoggingUtils

            # Remove old root logger from registry
            _logging_utils.removeLogger(_constants.ROOT_LOGGER_KEY)

            # Clear logging.root
            if hasattr(logging, "root"):
                logging.root = None  # type: ignore[assignment]

            # Set the logger class before getting the root logger
            # This ensures the manager creates the root logger with the correct class
            logging.setLoggerClass(logger_class)

            # Create new root logger using the manager's getLogger method
            # The logger class is already set above, so this will create a logger
            # of type logger_class. We use the manager directly because it handles
            # root logger creation properly even when logging.root is None.
            new_root_logger = logging.Logger.manager.getLogger(
                _constants.ROOT_LOGGER_KEY
            )

            # Ensure root logger has correct name
            if new_root_logger.name != _constants.ROOT_LOGGER_NAME:
                new_root_logger.name = _constants.ROOT_LOGGER_NAME

            # Update logging.root
            if hasattr(logging, "root"):
                logging.root = new_root_logger  # type: ignore[assignment]

            # Also update logging.Logger.manager.root to point to new root logger
            # The manager's root must stay in sync with logging.root, otherwise
            # they reference different objects and child loggers may have incorrect
            # parent references.
            logging.Logger.manager.root = new_root_logger  # type: ignore[assignment]

            # Port state from old root logger to new one
            _logging_utils.portLoggerState(
                root_logger,
                new_root_logger,
                port_handlers=True,
                port_level=True,
            )

        # Mark that user has explicitly configured the root logger
        # This tells extendLoggingModule() not to touch the root logger
        # Set on both the logger module (package mode) and apathetic_logging module
        # (stitched mode). This ensures the flag is accessible in all runtime modes.
        # Also set on the shim module (apathetic_logging.logger) if it exists, as
        # serger creates separate module objects for submodule shims in stitched mode.
        logger_module = sys.modules.get(__name__)
        if logger_module is not None:
            logger_module._root_logger_user_configured = True  # type: ignore[attr-defined]  # noqa: SLF001
        namespace_module = sys.modules.get("apathetic_logging")
        if namespace_module is not None:
            namespace_module._root_logger_user_configured = True  # type: ignore[attr-defined]  # noqa: SLF001
        # Also set on the shim module for stitched mode compatibility
        logger_shim_module = sys.modules.get("apathetic_logging.logger")
        if logger_shim_module is not None:
            logger_shim_module._root_logger_user_configured = True  # type: ignore[attr-defined]  # noqa: SLF001

    def determineLogLevel(
        self,
        *,
        args: argparse.Namespace | None = None,
        root_log_level: str | None = None,
    ) -> str:
        """Resolve log level from CLI → env → root config → default."""
        _registry = ApatheticLogging_Internal_RegistryData
        _constants = ApatheticLogging_Internal_Constants
        args_level = getattr(args, "log_level", None)
        if args_level is not None:
            # cast_hint would cause circular dependency
            return cast("str", args_level).upper()

        # Check registered environment variables, or fall back to "LOG_LEVEL"
        # Access registry via namespace class MRO to ensure correct resolution
        # in both package and stitched builds
        namespace_module = sys.modules.get("apathetic_logging")
        if namespace_module is not None:
            namespace_class = getattr(namespace_module, "apathetic_logging", None)
            if namespace_class is not None:
                # Use namespace class MRO to access registry
                # (handles shadowed attributes correctly)
                registered_env_vars = getattr(
                    namespace_class,
                    "registered_internal_log_level_env_vars",
                    None,
                )
                registered_default = getattr(
                    namespace_class,
                    "registered_internal_default_log_level",
                    None,
                )
            else:
                # Fallback to direct registry access
                registry_cls = _registry
                registered_env_vars = (
                    registry_cls.registered_internal_log_level_env_vars
                )
                registered_default = registry_cls.registered_internal_default_log_level
        else:
            # Fallback to direct registry access
            registered_env_vars = _registry.registered_internal_log_level_env_vars
            registered_default = _registry.registered_internal_default_log_level

        env_vars_to_check = (
            registered_env_vars or _constants.DEFAULT_APATHETIC_LOG_LEVEL_ENV_VARS
        )
        for env_var in env_vars_to_check:
            env_log_level = os.getenv(env_var)
            if env_log_level:
                return env_log_level.upper()

        if root_log_level:
            return root_log_level.upper()

        # Use registered default, or fall back to module default
        default_level: str = (
            registered_default or _constants.DEFAULT_APATHETIC_LOG_LEVEL
        )
        return default_level.upper()

    @property
    def levelName(self) -> str:
        """Return the explicit level name set on this logger.

        This property returns the name of the level explicitly set on this logger
        (via self.level). For the effective level name (what's actually used,
        considering inheritance), use effectiveLevelName instead.

        See also: logging.getLevelName, effectiveLevelName
        """
        return self.getLevelName()

    @property
    def effectiveLevel(self) -> int:
        """Return the effective level (what's actually used).

        This property returns the effective logging level for this logger,
        considering inheritance from parent loggers. This is the preferred
        way to get the effective level. Also available via getEffectiveLevel()
        for stdlib compatibility.

        See also: logging.Logger.getEffectiveLevel, effectiveLevelName
        """
        return self.getEffectiveLevel()

    @property
    def effectiveLevelName(self) -> str:
        """Return the effective level name (what's actually used).

        This property returns the name of the effective logging level for this
        logger, considering inheritance from parent loggers. This is the
        preferred way to get the effective level name. Also available via
        getEffectiveLevelName() for consistency.

        See also: logging.getLevelName, effectiveLevel
        """
        return self.getEffectiveLevelName()

    @property
    def root(self) -> "ApatheticLogging_Internal_Logger.Logger" | logging.RootLogger:  # type: ignore[override, name-defined]  # noqa: UP037, F821
        """Return the root logger instance.

        This property overrides the standard library's ``logging.Logger.root``
        class attribute to provide better type hints. It returns the same root
        logger instance as the standard library.

        The root logger may be either:
        - An ``apathetic_logging.Logger`` if it was created after
          ``extendLoggingModule()`` was called (expected/common case)
        - A standard ``logging.RootLogger`` if it was created before
          ``extendLoggingModule()`` was called (fallback, see ROADMAP.md)

        Returns:
            The root logger instance (either ``apathetic_logging.Logger`` or
            ``logging.RootLogger``).

        Example:
            >>> logger = getLogger("mymodule")
            >>> # Access root logger with better type hints
            >>> logger.root.setLevel("debug")
            >>> logger.root.levelName
            'DEBUG'

        """
        _constants = ApatheticLogging_Internal_Constants
        return logging.getLogger(_constants.ROOT_LOGGER_KEY)

    def getLevel(self) -> int:
        """Return the explicit level set on this logger.

        This method returns the level explicitly set on this logger (via
        self.level). For the effective level (what's actually used, considering
        inheritance), use getEffectiveLevel() or the effectiveLevel property.

        Returns:
            The explicit level value (int) set on this logger.

        See also: level property, getEffectiveLevel

        """
        return self.level

    def getLevelName(self) -> str:
        """Return the explicit level name set on this logger.

        This method returns the name of the level explicitly set on this logger
        (via self.level). For the effective level name (what's actually used,
        considering inheritance), use getEffectiveLevelName() or the
        effectiveLevelName property.

        Returns:
            The explicit level name (str) set on this logger.

        See also: levelName property, getEffectiveLevelName

        """
        from .logging_utils import (  # noqa: PLC0415
            ApatheticLogging_Internal_LoggingUtils,
        )

        return ApatheticLogging_Internal_LoggingUtils.getLevelNameStr(self.level)

    def getEffectiveLevelName(self) -> str:
        """Return the effective level name (what's actually used).

        This method returns the name of the effective logging level for this
        logger, considering inheritance from parent loggers. Prefer the
        effectiveLevelName property for convenience, or use this method for
        consistency with getEffectiveLevel().

        Returns:
            The effective level name (str) for this logger.

        See also: effectiveLevelName property, getEffectiveLevel

        """
        from .logging_utils import (  # noqa: PLC0415
            ApatheticLogging_Internal_LoggingUtils,
        )

        return ApatheticLogging_Internal_LoggingUtils.getLevelNameStr(
            self.getEffectiveLevel(),
        )

    def errorIfNotDebug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Logs an exception with the real traceback starting from the caller.
        Only shows full traceback if debug/trace is enabled.
        """
        exc_info = kwargs.pop("exc_info", True)
        stacklevel = kwargs.pop("stacklevel", self.DEFAULT_STACKLEVEL)
        if self.isEnabledFor(logging.DEBUG):
            self.exception(
                msg,
                *args,
                exc_info=exc_info,
                stacklevel=stacklevel,
                **kwargs,
            )
        else:
            self.error(msg, *args, **kwargs)

    def criticalIfNotDebug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Logs an exception with the real traceback starting from the caller.
        Only shows full traceback if debug/trace is enabled.
        """
        exc_info = kwargs.pop("exc_info", True)
        stacklevel = kwargs.pop("stacklevel", self.DEFAULT_STACKLEVEL)
        if self.isEnabledFor(logging.DEBUG):
            self.exception(
                msg,
                *args,
                exc_info=exc_info,
                stacklevel=stacklevel,
                **kwargs,
            )
        else:
            self.critical(msg, *args, **kwargs)

    def colorize(
        self,
        text: str,
        color: str,
        *,
        enable_color: bool | None = None,
    ) -> str:
        """Apply ANSI color codes to text.

        Defaults to using the instance's enable_color setting.

        Args:
            text: Text to colorize
            color: ANSI color code
            enable_color: Override color setting, or None to use instance default

        Returns:
            Colorized text if enabled, otherwise original text

        """
        _constants = ApatheticLogging_Internal_Constants
        if enable_color is None:
            enable_color = self.enable_color
        return f"{color}{text}{_constants.ANSIColors.RESET}" if enable_color else text

    def trace(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a trace-level message (more verbose than DEBUG)."""
        _constants = ApatheticLogging_Internal_Constants
        if self.isEnabledFor(_constants.TRACE_LEVEL):
            self._log(_constants.TRACE_LEVEL, msg, args, **kwargs)

    def detail(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a detail-level message (more detailed than INFO)."""
        _constants = ApatheticLogging_Internal_Constants
        if self.isEnabledFor(_constants.DETAIL_LEVEL):
            self._log(
                _constants.DETAIL_LEVEL,
                msg,
                args,
                **kwargs,
            )

    def brief(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a brief-level message (less detailed than INFO)."""
        _constants = ApatheticLogging_Internal_Constants
        if self.isEnabledFor(_constants.BRIEF_LEVEL):
            self._log(
                _constants.BRIEF_LEVEL,
                msg,
                args,
                **kwargs,
            )

    def test(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a test-level message (most verbose, bypasses capture)."""
        _constants = ApatheticLogging_Internal_Constants
        if self.isEnabledFor(_constants.TEST_LEVEL):
            self._log(_constants.TEST_LEVEL, msg, args, **kwargs)

    def logDynamic(self, level: str | int, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a message with a dynamically provided log level
           (unlike .info(), .error(), etc.).

        Useful when you have a log level (string or numeric) and don't want to resolve
        either the string to int, or the int to a log method.

        Args:
            level: Log level as string name or integer
            msg: Message format string
            *args: Arguments for message formatting
            **kwargs: Additional keyword arguments

        """
        # Resolve level
        if isinstance(level, str):
            from .logging_utils import (  # noqa: PLC0415
                ApatheticLogging_Internal_LoggingUtils,
            )

            try:
                level_no = ApatheticLogging_Internal_LoggingUtils.getLevelNumber(level)
            except ValueError:
                self.error("Unknown log level: %r", level)
                return
        elif isinstance(level, int):  # pyright: ignore[reportUnnecessaryIsInstance]
            level_no = level
        else:
            self.error("Invalid log level type: %r", type(level))
            return

        self._log(level_no, msg, args, **kwargs)

    @contextmanager
    def useLevel(
        self,
        level: str | int,
        *,
        minimum: bool = False,
    ) -> Generator[None, None, None]:
        """Use a context to temporarily log with a different log-level.

        Args:
            level: Log level to use (string name or numeric value)
            minimum: If True, only set the level if it's more verbose (lower
                numeric value) than the current effective level. This prevents
                downgrading from a more verbose level (e.g., TRACE) to a less
                verbose one (e.g., DEBUG). Compares against effective level
                (considering parent inheritance), matching setLevel(minimum=True)
                behavior. Defaults to False.

        Yields:
            None: Context manager yields control to the with block

        """
        # Save explicit level for restoration (not effective level)
        prev_level = self.level

        # Resolve level
        if isinstance(level, str):
            from .logging_utils import (  # noqa: PLC0415
                ApatheticLogging_Internal_LoggingUtils,
            )

            try:
                level_no = ApatheticLogging_Internal_LoggingUtils.getLevelNumber(level)
            except ValueError:
                self.error("Unknown log level: %r", level)
                # Yield control anyway so the 'with' block doesn't explode
                yield
                return
        elif isinstance(level, int):  # pyright: ignore[reportUnnecessaryIsInstance]
            level_no = level
        else:
            self.error("Invalid log level type: %r", type(level))
            yield
            return

        # Apply new level (only if more verbose when minimum=True)
        if minimum:
            # Compare against effective level (not explicit level) to match
            # setLevel(minimum=True) behavior. This ensures consistent behavior
            # when logger inherits level from parent.
            current_effective_level = self.getEffectiveLevel()
            # Lower number = more verbose, so only set if new level is more verbose
            if level_no < current_effective_level:
                self.setLevel(level_no)
            # Otherwise keep current level (don't downgrade)
        else:
            self.setLevel(level_no)

        try:
            yield
        finally:
            self.setLevel(prev_level)

    @contextmanager
    def useLevelMinimum(self, level: str | int) -> Generator[None, None, None]:
        """Use a context to temporarily log with a different log-level.

        Only applies if the level is more verbose than the current level.

        This convenience context manager is equivalent to calling
        ``useLevel(level, minimum=True)``. It temporarily sets the logger level
        only if the requested level is more verbose (lower numeric value) than
        the current effective level, preventing downgrades from more verbose
        levels.

        Args:
            level: Log level to use (string name or numeric value). Only applied
                if it's more verbose than the current effective level.

        Yields:
            None: Context manager yields control to the with block

        Example:
            >>> logger = getLogger("mymodule")
            >>> logger.setLevel("TRACE")
            >>> # This won't downgrade from TRACE to DEBUG
            >>> with logger.useLevelMinimum("DEBUG"):
            ...     assert logger.levelName == "TRACE"  # Still TRACE
            >>> # This will upgrade from INFO to DEBUG
            >>> logger.setLevel("INFO")
            >>> with logger.useLevelMinimum("DEBUG"):
            ...     assert logger.levelName == "DEBUG"  # Upgraded to DEBUG

        """
        with self.useLevel(level, minimum=True):
            yield

    @contextmanager
    def usePropagate(
        self,
        propagate: bool,  # noqa: FBT001
        *,
        manage_handlers: bool | None = None,
    ) -> Generator[None, None, None]:
        """Use a context to temporarily change propagate setting.

        Args:
            propagate: If True, messages propagate to parent loggers. If False,
                messages only go to this logger's handlers.
            manage_handlers: If True, automatically manage apathetic handlers
                based on propagate setting. If None, uses DEFAULT_MANAGE_HANDLERS
                from constants. If False, only sets propagate without managing handlers.
                In compat_mode, this may default to False.

        Yields:
            None: Context manager yields control to the with block

        """
        # Save current propagate setting for restoration
        prev_propagate = self.propagate

        # Apply new propagate setting
        self.setPropagate(propagate, manage_handlers=manage_handlers)

        try:
            yield
        finally:
            # Restore previous propagate setting
            self.setPropagate(prev_propagate, manage_handlers=manage_handlers)

    @contextmanager
    def useLevelAndPropagate(
        self,
        level: str | int,
        *,
        minimum: bool = False,
        manage_handlers: bool | None = None,
    ) -> Generator[None, None, None]:
        """Use a context to temporarily set level and propagate together.

        This convenience context manager combines useLevel() and usePropagate()
        with intelligent defaults:
        - If level is INHERIT_LEVEL (NOTSET): sets propagate=True
        - If level is a specific level: sets propagate=False
        - On root logger: only sets level (propagate is unchanged)

        Both settings are restored when the context exits.

        Args:
            level: Log level to use (string name or numeric value). Use
                INHERIT_LEVEL (0) or "NOTSET" to inherit.
            minimum: If True, only set the level if it's more verbose (lower
                numeric value) than the current effective level. This prevents
                downgrading from a more verbose level (e.g., TRACE) to a less
                verbose one (e.g., DEBUG). Compares against effective level
                (considering parent inheritance), matching setLevel(minimum=True)
                behavior. Defaults to False.
            manage_handlers: If True, automatically manage apathetic handlers
                based on propagate setting. If None, uses DEFAULT_MANAGE_HANDLERS
                from constants. If False, only sets propagate without managing handlers.
                In compat_mode, this may default to False.

        Yields:
            None: Context manager yields control to the with block

        Example:
            >>> logger = getLogger("mymodule")
            >>> # Temporarily inherit level and propagate
            >>> with logger.useLevelAndPropagate(INHERIT_LEVEL):
            ...     logger.info("This propagates to root")
            >>> # Temporarily set explicit level with isolated logging
            >>> with logger.useLevelAndPropagate("debug"):
            ...     logger.debug("This only goes to logger's handlers")

        """
        from .logging_utils import (  # noqa: PLC0415
            ApatheticLogging_Internal_LoggingUtils,
        )

        _constants = ApatheticLogging_Internal_Constants

        # Save current settings for restoration
        prev_level = self.level
        prev_propagate = self.propagate

        # Resolve level
        if isinstance(level, str):
            _logging_utils = ApatheticLogging_Internal_LoggingUtils
            try:
                level_no = _logging_utils.getLevelNumber(level)
            except ValueError:
                self.error("Unknown log level: %r", level)
                # Yield control anyway so the 'with' block doesn't explode
                yield
                return
        elif isinstance(level, int):  # pyright: ignore[reportUnnecessaryIsInstance]
            level_no = level
        else:
            self.error("Invalid log level type: %r", type(level))
            yield
            return

        # Apply new level (only if more verbose when minimum=True)
        if minimum:
            # Compare against effective level (not explicit level) to match
            # setLevel(minimum=True) behavior. This ensures consistent behavior
            # when logger inherits level from parent.
            current_effective_level = self.getEffectiveLevel()
            # Lower number = more verbose, so only set if new level is more verbose
            if level_no < current_effective_level:
                self.setLevel(level_no)
            # Otherwise keep current level (don't downgrade)
        else:
            self.setLevel(level_no)

        # Set propagate based on level (only if not root logger)
        # Root logger can have name "" (ROOT_LOGGER_KEY) or "root" (ROOT_LOGGER_NAME)
        is_root = self.name in {
            _constants.ROOT_LOGGER_KEY,
            _constants.ROOT_LOGGER_NAME,
        }
        if not is_root:
            if level_no == _constants.INHERIT_LEVEL:
                # INHERIT_LEVEL -> propagate=True
                self.setPropagate(True, manage_handlers=manage_handlers)
            else:
                # Specific level -> propagate=False
                self.setPropagate(False, manage_handlers=manage_handlers)
        # Root logger: propagate is unchanged (root always has handlers)

        try:
            yield
        finally:
            # Restore previous settings
            self.setLevel(prev_level)
            if not is_root:
                self.setPropagate(prev_propagate, manage_handlers=manage_handlers)
