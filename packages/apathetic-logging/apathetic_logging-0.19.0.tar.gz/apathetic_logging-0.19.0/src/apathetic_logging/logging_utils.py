# src/apathetic_logging/logging_utils.py
"""Logging utilities for Apathetic Logging.

Docstrings are adapted from the standard library logging module documentation
licensed under the Python Software Foundation License Version 2.
"""

from __future__ import annotations

import inspect
import logging
import sys
from types import FrameType
from typing import Any, TypeVar

from .constants import (
    ApatheticLogging_Internal_Constants,
)


class ApatheticLogging_Internal_LoggingUtils:  # noqa: N801  # pyright: ignore[reportUnusedClass]
    """Mixin class that provides helper functions for the standard logging module.

    This class contains utility functions that operate directly on or replace
    standard library `logging.*` utilities and functions. These helpers extend
    or wrap the built-in logging module functionality to provide enhanced
    capabilities or safer alternatives.

    When mixed into apathetic_logging, it provides utility functions that
    interact with Python's standard logging module.
    """

    _LoggerType = TypeVar("_LoggerType", bound=logging.Logger)

    @staticmethod
    def _getCompatibilityMode() -> bool:
        """Get the compatibility mode setting from registry.

        Returns the registered compatibility mode setting, or False (improved
        behavior) if not registered. This is an internal helper to avoid
        circular imports (registry.py imports from logging_utils.py).

        Returns:
            Compatibility mode setting (True or False).
            Defaults to False if not registered.
        """
        from .registry_data import (  # noqa: PLC0415
            ApatheticLogging_Internal_RegistryData,
        )

        _registry_data = ApatheticLogging_Internal_RegistryData
        return (
            _registry_data.registered_internal_compatibility_mode
            if _registry_data.registered_internal_compatibility_mode is not None
            else False
        )

    @staticmethod
    def getLevelName(
        level: int | str, *args: Any, strict: bool = False, **kwargs: Any
    ) -> str | int:
        """Return the textual or numeric representation of a logging level.

        Behavior depends on compatibility mode (set via `registerCompatibilityMode()`):

        - Value-add: Uppercases string inputs before processing

        **Compatibility mode disabled (`compat_mode=False`, default):**
        - Accepts both integer and string input
        - For string input: validates level exists and returns canonical
          level name string
        - For integer input: returns level name as string (never returns `int`)
        - Optional strict mode to raise `ValueError` for unknown integer levels

        For string→int conversion, use `getLevelNumber()` instead.

        **Compatibility mode enabled (`compat_mode=True`):**
        - Behaves like stdlib `logging.getLevelName()` (bidirectional)
        - Returns `str` for integer input, `int` for string input (known levels)
        - Returns `"Level {level}"` string for unknown levels

        Args:
            level: Log level as integer or string name
            *args: Additional positional arguments (for future-proofing)
            strict: If True, raise ValueError for unknown levels. If False (default),
                returns "Level {level}" format for unknown integer levels (matching
                stdlib behavior). Only used when compatibility mode is disabled and
                level is an integer.
            **kwargs: Additional keyword arguments (for future-proofing)

        Returns:
            - Compatibility mode enabled: `str | int` (bidirectional like stdlib)
            - Compatibility mode disabled: `str` (always string; string input
              is validated and returns canonical name, int input is converted
              to name)

        Raises:
            ValueError: If string level cannot be resolved to a known level
                (non-compat mode), or if strict=True and level is an integer
                that cannot be resolved to a known level name

        Example:
            >>> # Compatibility mode enabled (stdlib-like behavior):
            >>> from apathetic_logging import registerCompatibilityMode
            >>> registerCompatibilityMode(compat_mode=True)
            >>> getLevelName(10)  # int input
            "DEBUG"
            >>> getLevelName("DEBUG")  # string input
            10
            >>> getLevelName("debug")  # case-insensitive, uppercased
            10

            >>> # Compatibility mode disabled (improved behavior):
            >>> registerCompatibilityMode(compat_mode=False)
            >>> getLevelName(10)
            "DEBUG"
            >>> getLevelName("DEBUG")  # Validates and returns canonical name
            "DEBUG"
            >>> getLevelName("debug")  # Validates and returns canonical name
            "DEBUG"
            >>> getLevelName("UNKNOWN")  # Unknown string raises ValueError
            ValueError: Unknown log level: 'UNKNOWN'

        See Also:
            getLevelNumber() - Convert string to int (when compat mode disabled)
            registerCompatibilityMode() - Enable/disable compatibility mode

        https://docs.python.org/3.10/library/logging.html#logging.getLevelName
        """
        # Check compatibility mode from registry
        compat_mode = ApatheticLogging_Internal_LoggingUtils._getCompatibilityMode()

        # Use unidirectional functions to avoid duplication
        if compat_mode and isinstance(level, str):
            # Compatibility mode with string input → return int (like stdlib)
            return ApatheticLogging_Internal_LoggingUtils.getLevelNumber(level)

        # All other cases: return string (compat mode with int, or non-compat mode)
        return ApatheticLogging_Internal_LoggingUtils.getLevelNameStr(
            level, *args, strict=strict, **kwargs
        )

    @staticmethod
    def getLevelNumber(level: str | int) -> int:
        """Convert a log level name to its numeric value.

        Recommended way to convert string level names to integers. This function
        explicitly performs string->int conversion, unlike `getLevelName()` which
        has bidirectional behavior for backward compatibility.

        Handles all levels registered via logging.addLevelName() (including
        standard library levels, custom apathetic levels, and user-registered levels).

        Args:
            level: Log level as string name (case-insensitive) or integer

        Returns:
            Integer level value

        Raises:
            ValueError: If level cannot be resolved to a known level

        Example:
            >>> getLevelNumber("DEBUG")
            10
            >>> getLevelNumber("TRACE")
            5
            >>> getLevelNumber(20)
            20
            >>> getLevelNumber("UNKNOWN")
            ValueError: Unknown log level: 'UNKNOWN'

        See Also:
            getLevelName() - Convert int to string (intended use)
        """
        if isinstance(level, int):
            return level

        level_str = level.upper()

        # Use getattr() to find level constants registered via logging.addLevelName():
        # - Standard library levels (DEBUG, INFO, etc.) - registered by default
        # - Custom apathetic levels (TEST, TRACE, etc.)
        #   registered via extendLoggingModule()
        # - User-registered levels via our addLevelName() method
        #   (but not stdlib's logging.addLevelName() which doesn't set attribute)
        # - User-registered levels via setattr(logging, level_str, value)
        resolved = getattr(logging, level_str, None)
        if isinstance(resolved, int):
            return resolved

        # Unknown level: always raise
        msg = f"Unknown log level: {level_str!r}"
        raise ValueError(msg)

    @staticmethod
    def getLevelNameStr(
        level: int | str, *args: Any, strict: bool = False, **kwargs: Any
    ) -> str:
        """Convert a log level to its string name representation.

        Unidirectional function that always returns a string. This is the recommended
        way to convert log levels to strings when you want guaranteed string output
        without compatibility mode behavior.

        Unlike `getLevelName()` which has compatibility mode and bidirectional
        behavior, this function always returns a string:
        - Integer input: converts to level name string (returns "Level {level}"
          for unknown levels unless strict=True)
        - String input: validates level exists, then returns uppercased string

        Handles all levels registered via logging.addLevelName() (including
        standard library levels, custom apathetic levels, and user-registered levels).

        Args:
            level: Log level as integer or string name (case-insensitive)
            *args: Additional positional arguments (for future-proofing)
            strict: If True, raise ValueError for unknown integer levels.
                If False (default), returns "Level {level}" format for unknown
                integer levels (matching stdlib behavior).
            **kwargs: Additional keyword arguments (for future-proofing)

        Returns:
            Level name as uppercase string

        Raises:
            ValueError: If string level cannot be resolved to a known level,
                or if strict=True and integer level cannot be resolved to a
                known level

        Example:
            >>> getLevelNameStr(10)
            "DEBUG"
            >>> getLevelNameStr(5)
            "TRACE"
            >>> getLevelNameStr("DEBUG")
            "DEBUG"
            >>> getLevelNameStr("debug")
            "DEBUG"
            >>> getLevelNameStr(999)  # Unknown integer, strict=False (default)
            "Level 999"
            >>> getLevelNameStr(999, strict=True)  # Unknown integer, strict=True
            ValueError: Unknown log level: 999
            >>> getLevelNameStr("UNKNOWN")
            ValueError: Unknown log level: 'UNKNOWN'

        See Also:
            getLevelNumber() - Convert string to int (complementary function)
            getLevelName() - Bidirectional conversion with compatibility mode
        """
        # If string input, validate it exists and return canonical name
        if isinstance(level, str):
            # Validate level exists (raises ValueError if not)
            ApatheticLogging_Internal_LoggingUtils.getLevelNumber(level)
            return level.upper()

        # Integer input: convert to level name string
        result = logging.getLevelName(level, *args, **kwargs)
        # logging.getLevelName always returns str for int input

        # If input was int and result is "Level {level}" format and strict is on, raise
        if result.startswith("Level ") and strict:
            msg = f"Unknown log level: {level}"
            raise ValueError(msg)

        # level name or (strict=False) "Level {int}"
        return result

    @staticmethod
    def hasLogger(logger_name: str) -> bool:
        """Check if a logger exists in the logging manager's registry.

        Args:
            logger_name: The name of the logger to check.

        Returns:
            True if the logger exists in the registry, False otherwise.
        """
        return logger_name in logging.Logger.manager.loggerDict

    @staticmethod
    def reconnectChildLoggers(
        old_logger: logging.Logger,
        new_logger: logging.Logger,
    ) -> None:
        """Reconnect child loggers from old logger to new logger.

        When a logger is replaced, child loggers maintain a direct reference
        to their parent. This function updates all child loggers to point to
        the new logger instance.

        Args:
            old_logger: The logger being replaced.
            new_logger: The new logger that should become the parent.
        """
        _constants = ApatheticLogging_Internal_Constants

        for logger_name, logger in logging.Logger.manager.loggerDict.items():
            # Skip if not a Logger instance
            if not isinstance(logger, logging.Logger):
                continue

            # Skip the new logger itself
            if logger is new_logger:
                continue

            # For root logger replacement, skip if logger name is root logger
            # key/name (shouldn't happen, but be safe)
            old_logger_name = old_logger.name
            root_names = {_constants.ROOT_LOGGER_KEY, _constants.ROOT_LOGGER_NAME}
            if old_logger_name in root_names and logger_name in root_names:
                continue

            # Check if this logger's parent is the old logger
            # For root logger, any logger with a name is a child
            # For named loggers, children have names starting with parent_name + "."
            is_child = False
            if old_logger_name in root_names:
                # Root logger - any logger with a name is a child
                is_child = logger_name not in root_names
            else:
                # Named logger - child names start with parent_name + "."
                is_child = logger_name.startswith(old_logger_name + ".")

            if is_child and logger.parent is old_logger:
                logger.parent = new_logger

    @staticmethod
    def _portPropagateAndDisabled(
        old_logger: logging.Logger,
        new_logger: logging.Logger,
    ) -> None:
        """Port propagate and disabled state from old logger to new logger."""
        # Use setPropagate() if available to set the _propagate_explicit flag
        # (prevents _applyPropagateSetting() from overriding ported value)
        if hasattr(new_logger, "setPropagate"):
            new_logger.setPropagate(old_logger.propagate)  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
        else:
            new_logger.propagate = old_logger.propagate
        new_logger.disabled = old_logger.disabled

    @staticmethod
    def _portHandlers(
        old_logger: logging.Logger,
        new_logger: logging.Logger,
    ) -> None:
        """Port handlers from old logger to new logger."""
        old_handlers = list(old_logger.handlers)  # Copy list
        for handler in old_handlers:
            new_logger.addHandler(handler)

    @staticmethod
    def _portLevel(
        old_logger: logging.Logger,
        new_logger: logging.Logger,
    ) -> None:
        """Port level from old logger to new logger."""
        old_level = old_logger.level
        # Validate level if it's an apathetic logger (has validateLevel)
        if hasattr(new_logger, "validateLevel"):
            try:
                new_logger.validateLevel(old_level)  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
            except ValueError:
                # Invalid level - fall back to apathetic default
                return

        # Set the level - NOTSET/INHERIT_LEVEL (0) is always allowed
        if hasattr(new_logger, "setLevel"):
            new_logger.setLevel(old_level)
        else:
            new_logger.level = old_level

    @staticmethod
    def _setApatheticDefaults(
        new_logger: logging.Logger,
    ) -> None:
        """Set apathetic defaults for logger level."""
        _constants = ApatheticLogging_Internal_Constants
        root_names = {_constants.ROOT_LOGGER_KEY, _constants.ROOT_LOGGER_NAME}
        is_root = new_logger.name in root_names
        if is_root:
            # Root logger: use determineLogLevel() if available
            if hasattr(new_logger, "determineLogLevel"):
                level_name = new_logger.determineLogLevel()  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType, reportUnknownVariableType]
                new_logger.setLevel(level_name)  # pyright: ignore[reportUnknownArgumentType]
            else:
                # Fallback: use INHERIT_LEVEL (though root has no parent)
                new_logger.setLevel(_constants.INHERIT_LEVEL)
        # Leaf logger: use INHERIT_LEVEL to inherit from parent
        elif hasattr(new_logger, "setLevel"):
            new_logger.setLevel(_constants.INHERIT_LEVEL)
        else:
            new_logger.level = _constants.INHERIT_LEVEL

    @staticmethod
    def portLoggerState(
        old_logger: logging.Logger,
        new_logger: logging.Logger,
        *,
        port_handlers: bool | None = None,
        port_level: bool | None = None,
    ) -> None:
        """Port state from old logger to new logger.

        Ports propagate and disabled state always. Optionally ports handlers
        and level based on parameters. When not porting level, uses apathetic
        defaults: determineLogLevel() for root logger, INHERIT_LEVEL for leaf loggers.

        After porting (or not porting) handlers, calls manageHandlers() if the new
        logger supports it, to ensure apathetic handlers are set up appropriately
        based on propagate setting. This ensures root logger always has a handler,
        and child loggers with propagate=False get handlers as needed. manageHandlers()
        only manages DualStreamHandler instances, so it won't interfere with ported
        user handlers.

        Finally, reconnects child loggers from the old logger to the new logger,
        ensuring child loggers point to the new logger instance after replacement.

        Args:
            old_logger: The logger being replaced.
            new_logger: The new logger to port state to.
            port_handlers: Whether to port handlers. If None, checks registry setting
                or defaults to True. When True, handlers from old logger are ported.
                When False, new logger manages its own handlers via manageHandlers().
                In both cases, manageHandlers() is called to ensure apathetic handlers
                are set up if needed.
            port_level: Whether to port level. If None, checks registry setting or
                defaults to True. When True, level from old logger is ported.
                When False, uses apathetic defaults (determineLogLevel() for root,
                INHERIT_LEVEL for leaf loggers). Note: User-provided level parameters
                in getLogger/getLoggerOfType take precedence over ported level.
        """
        from .constants import (  # noqa: PLC0415
            ApatheticLogging_Internal_Constants,
        )
        from .registry_data import (  # noqa: PLC0415
            ApatheticLogging_Internal_RegistryData,
        )

        _constants = ApatheticLogging_Internal_Constants
        _registry_data = ApatheticLogging_Internal_RegistryData

        # Always port propagate and disabled
        ApatheticLogging_Internal_LoggingUtils._portPropagateAndDisabled(
            old_logger, new_logger
        )

        # Resolve port_handlers parameter
        if port_handlers is None:
            port_handlers = (
                _registry_data.registered_internal_port_handlers
                if _registry_data.registered_internal_port_handlers is not None
                else _constants.DEFAULT_PORT_HANDLERS
            )

        # Port handlers if requested
        if port_handlers:
            ApatheticLogging_Internal_LoggingUtils._portHandlers(old_logger, new_logger)

        # After porting (or not porting) handlers, ensure apathetic handlers are set up
        # if the logger supports manageHandlers(). This ensures root logger always has
        # a handler, and child loggers with propagate=False get handlers as needed.
        # manageHandlers() only manages DualStreamHandler instances, so it won't
        # interfere with ported user handlers.
        if hasattr(new_logger, "manageHandlers"):
            new_logger.manageHandlers()  # pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]

        # Resolve port_level parameter
        if port_level is None:
            port_level = (
                _registry_data.registered_internal_port_level
                if _registry_data.registered_internal_port_level is not None
                else _constants.DEFAULT_PORT_LEVEL
            )

        # Port level if requested, otherwise use apathetic defaults
        if port_level:
            ApatheticLogging_Internal_LoggingUtils._portLevel(old_logger, new_logger)
        else:
            ApatheticLogging_Internal_LoggingUtils._setApatheticDefaults(new_logger)

        # Reconnect child loggers from old logger to new logger
        # This ensures child loggers point to the new logger instance after replacement
        ApatheticLogging_Internal_LoggingUtils.reconnectChildLoggers(
            old_logger, new_logger
        )

    @staticmethod
    def removeLogger(logger_name: str) -> None:
        """Remove a logger from the logging manager's registry.

        Args:
            logger_name: The name of the logger to remove.
        """
        logging.Logger.manager.loggerDict.pop(logger_name, None)

    @staticmethod
    def _extractTopLevelPackage(package: str | None) -> str | None:
        """Extract top-level package name from package string.

        Args:
            package: Package string (e.g., "myapp.submodule") or None

        Returns:
            Top-level package name (e.g., "myapp") or None if package is None
        """
        if package is None:
            return None
        if "." in package:
            return package.split(".", 1)[0]
        return package

    @staticmethod
    def _inferFromFrame(skip_frames: int, frame: FrameType | None) -> str | None:
        """Infer logger name from caller's frame.

        Args:
            skip_frames: Number of frames to skip to get to actual caller
            frame: Frame to start from, or None

        Returns:
            Inferred logger name or None if cannot be inferred
        """
        if frame is None:
            return None
        try:
            # Skip the specified number of frames to get to the actual caller
            caller_frame = frame.f_back
            for _ in range(skip_frames):
                if caller_frame is None:
                    break
                caller_frame = caller_frame.f_back
            if caller_frame is None:
                return None
            caller_package = caller_frame.f_globals.get("__package__")
            return ApatheticLogging_Internal_LoggingUtils._extractTopLevelPackage(
                caller_package
            )
        finally:
            del frame

    @staticmethod
    def getDefaultLoggerName(
        logger_name: str | None = None,
        *,
        check_registry: bool = True,
        skip_frames: int = 1,
        raise_on_error: bool = False,
        infer: bool = True,
        register: bool = False,
    ) -> str | None:
        """Get default logger name with optional inference from caller's frame.

        This function handles the common pattern of:
        1. Using explicit name if provided
        2. Checking registry if requested
        3. Inferring from caller's frame if needed (when infer=True)
        4. Storing inferred name in registry (when register=True)
        5. Returning None or raising error if still unresolved

        Args:
            logger_name: Explicit logger name, or None to infer.
            check_registry: If True, check registry before inferring. Use False
                when the caller should actively determine the name from current
                context (e.g., registerLogger() which should re-infer even
                if a name is already registered). Use True when the caller should
                use a previously registered name if available (e.g., getLogger()
                which should use the registered name).
            skip_frames: Number of frames to skip from this function to get to
                the actual caller. Default is 1 (skips this function's frame).
            raise_on_error: If True, raise RuntimeError if logger name cannot be
                resolved. If False (default), return None instead. Use True when
                a logger name is required (e.g., when creating a logger).
            infer: If True (default), attempt to infer logger name from caller's
                frame when not found in registry. If False, skip inference and
                return None if not found in registry.
            register: If True, store inferred name in registry. If False (default),
                do not modify registry. Note: Explicit names are never stored regardless
                of this parameter.

        Returns:
            Resolved logger name, or None if cannot be resolved and
            raise_on_error=False.

        Raises:
            RuntimeError: If logger name cannot be resolved and raise_on_error=True.
        """
        # Import locally to avoid circular import
        from .registry_data import (  # noqa: PLC0415
            ApatheticLogging_Internal_RegistryData,
        )

        _registry_data = ApatheticLogging_Internal_RegistryData

        # If explicit name provided, return it (never store explicit names)
        # Note: Empty string ("") is a special case - it represents the root logger
        # and is returned as-is to match standard library behavior.
        if logger_name is not None:
            return logger_name

        # Check registry if requested
        if check_registry:
            registered_name = _registry_data.registered_internal_logger_name
            if registered_name is not None:
                return registered_name

        # Try to infer from caller's frame if inference is enabled
        if not infer:
            # Inference disabled - return None or raise error
            if raise_on_error:
                error_msg = (
                    "Cannot resolve logger name: not in registry and inference "
                    "is disabled. Please call registerLogger() with an "
                    "explicit logger name or enable inference."
                )
                raise RuntimeError(error_msg)
            return None

        # Get current frame (this function's frame) and skip to caller
        frame = inspect.currentframe()
        inferred_name = ApatheticLogging_Internal_LoggingUtils._inferFromFrame(
            skip_frames, frame
        )

        # Store inferred name in registry if requested
        if inferred_name is not None and register:
            _registry_data.registered_internal_logger_name = inferred_name

        # Return inferred name or handle error
        if inferred_name is not None:
            return inferred_name

        # Handle error case
        if raise_on_error:
            error_msg = (
                "Cannot auto-infer logger name: __package__ is not set in the "
                "calling module. Please call registerLogger() with an "
                "explicit logger name."
            )
            raise RuntimeError(error_msg)

        return None

    @staticmethod
    def checkPythonVersionRequirement(
        required_version: tuple[int, int],
        function_name: str,
    ) -> None:
        """Check if the target or runtime Python version meets the requirement.

        This method validates that a function requiring a specific Python version
        can be called safely. It checks:
        1. Target version (if set via registerTargetPythonVersion), otherwise
           falls back to TARGET_PYTHON_VERSION from constants
        2. Runtime version (as a safety net to catch actual runtime issues)

        This allows developers to catch version incompatibilities during development
        even when running on a newer Python version than their target.

        Args:
            required_version: Target Python version required (major, minor) tuple
            function_name: Name of the function being checked (for error messages)

        Raises:
            NotImplementedError: If target version or runtime version doesn't meet
                the requirement. Error message includes guidance on raising target
                version if applicable.

        Example:
            >>> checkPythonVersionRequirement((3, 11), "get_level_names_mapping")
            # Raises if target version < 3.11 or runtime version < 3.11
        """
        # Import locally to avoid circular imports
        from .constants import (  # noqa: PLC0415
            ApatheticLogging_Internal_Constants,
        )
        from .registry_data import (  # noqa: PLC0415
            ApatheticLogging_Internal_RegistryData,
        )

        _constants = ApatheticLogging_Internal_Constants
        _registry_data = ApatheticLogging_Internal_RegistryData

        # Determine effective target version
        # If target version is set, use it; otherwise fall back to TARGET_PYTHON_VERSION
        target_version = _registry_data.registered_internal_target_python_version
        if target_version is None:
            target_version = _constants.TARGET_PYTHON_VERSION

        # Check target version first (primary check)
        # Skip check if target_version is None (checks disabled)
        if target_version is not None and target_version < required_version:
            req_major, req_minor = required_version
            tgt_major, tgt_minor = target_version
            msg = (
                f"{function_name} requires Python {req_major}.{req_minor}+, "
                f"but target version is {tgt_major}.{tgt_minor}. "
                f"To use this function, call "
                f"registerTargetPythonVersion(({req_major}, {req_minor})) "
                f"or raise your target version to at least {req_major}.{req_minor}."
            )
            raise NotImplementedError(msg)

        # Check runtime version as safety net
        runtime_version = (sys.version_info.major, sys.version_info.minor)
        if runtime_version < required_version:
            req_major, req_minor = required_version
            rt_major, rt_minor = runtime_version
            msg = (
                f"{function_name} requires Python {req_major}.{req_minor}+, "
                f"but runtime version is {rt_major}.{rt_minor}. "
                f"This function is not available in your Python version."
            )
            raise NotImplementedError(msg)
