# src/apathetic_logging/logging_root.py
"""Root logger convenience API for applications using root logger as source of truth.

This module provides a set of functions that operate on the root logger directly.
This API is designed for applications that use the root logger as the single source
of truth for log levels, with child loggers inheriting via NOTSET/INHERIT_LEVEL.

By providing a complete root-logger-specific API, we prevent users from accidentally
mixing root logger operations with child logger operations, which can lead to hard
to trace bugs.
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any


class ApatheticLogging_Internal_LoggingRoot:  # noqa: N801
    """Mixin providing root logger convenience methods.

    These functions operate directly on the root logger and provide utilities
    for applications that use root logger as the single source of truth for
    log levels.

    This prevents users from accidentally using child logger methods when they
    meant to use root logger methods, which is a common source of hard-to-trace bugs.
    """

    @staticmethod
    def getRootLogger() -> logging.Logger:  # May be Logger or RootLogger
        """Return the root logger instance.

        This is the primary way to access the root logger. It's more explicit
        and discoverable than using ``logging.getLogger("")`` or
        ``getLogger("")``.

        The root logger may be either:
        - An ``apathetic_logging.Logger`` if it was created after
          ``extendLoggingModule()`` was called (expected/common case)
        - A standard ``logging.RootLogger`` if it was created before
          ``extendLoggingModule()`` was called (fallback, see ROADMAP.md)

        Returns:
            The root logger instance (either ``apathetic_logging.Logger`` or
            ``logging.RootLogger``).

        Example:
            >>> from apathetic_logging import getRootLogger
            >>> root = getRootLogger()
            >>> root.setLevel("debug")
            >>> root.info("This logs to the root logger")
        """
        from .constants import (  # noqa: PLC0415
            ApatheticLogging_Internal_Constants,
        )

        _constants = ApatheticLogging_Internal_Constants
        return logging.getLogger(_constants.ROOT_LOGGER_KEY)

    @staticmethod
    def getRootLevel() -> int:
        """Return the current explicit log level set on the root logger.

        This is the level set on the root logger itself, not considering any
        parent (the root logger has no parent). For the effective level (which
        would be the same for root), use getEffectiveRootLevel().

        Returns:
            Integer log level value. Returns logging.NOTSET (0) if root logger
            has not had its level explicitly set.

        Example:
            >>> getRootLevel()
            10  # DEBUG
            >>> getRootLevelName()
            "DEBUG"

        See Also:
            getEffectiveRootLevel() - Returns effective level (same as explicit
                for root)
            getEffectiveRootLevelName() - Returns name of effective level
        """
        from .constants import (  # noqa: PLC0415
            ApatheticLogging_Internal_Constants,
        )

        _constants = ApatheticLogging_Internal_Constants
        root = logging.getLogger(_constants.ROOT_LOGGER_KEY)
        return root.level

    @staticmethod
    def getRootLevelName() -> str:
        """Return the name of the current explicit log level on the root logger.

        Returns the name of the level set on the root logger itself (e.g., "DEBUG",
        "INFO", "NOTSET"). For the name of the effective level, use
        getEffectiveRootLevelName().

        Returns:
            Level name as uppercase string (e.g., "DEBUG", "TRACE", "NOTSET").

        Raises:
            ValueError: If the level value is unknown (should not happen with
                standard and registered levels).

        Example:
            >>> getRootLevelName()
            "DEBUG"
            >>> getRootLevel()
            10

        See Also:
            getRootLevel() - Returns numeric level value
            getEffectiveRootLevelName() - Returns name of effective level
        """
        from .logging_utils import (  # noqa: PLC0415
            ApatheticLogging_Internal_LoggingUtils,
        )

        level = ApatheticLogging_Internal_LoggingRoot.getRootLevel()
        return ApatheticLogging_Internal_LoggingUtils.getLevelNameStr(level)

    @staticmethod
    def getEffectiveRootLevel() -> int:
        """Return the effective log level on the root logger.

        For the root logger, this is the same as the explicit level since the
        root logger has no parent to inherit from. This method exists for API
        completeness and symmetry with Logger.getEffectiveLevel().

        Returns:
            Integer log level value.

        Example:
            >>> getEffectiveRootLevel()
            10  # DEBUG

        See Also:
            getRootLevel() - Returns explicit level on root
            getEffectiveRootLevelName() - Returns name of effective level
        """
        from .constants import (  # noqa: PLC0415
            ApatheticLogging_Internal_Constants,
        )

        _constants = ApatheticLogging_Internal_Constants
        root = logging.getLogger(_constants.ROOT_LOGGER_KEY)
        return root.getEffectiveLevel()

    @staticmethod
    def getEffectiveRootLevelName() -> str:
        """Return the name of the effective log level on the root logger.

        For the root logger, this is the same as the explicit level name.
        This method exists for API completeness and symmetry with
        Logger.getEffectiveLevelName().

        Returns:
            Level name as uppercase string (e.g., "DEBUG", "TRACE", "NOTSET").

        Example:
            >>> getEffectiveRootLevelName()
            "DEBUG"

        See Also:
            getRootLevelName() - Returns name of explicit level
            getEffectiveRootLevel() - Returns numeric effective level
        """
        from .logging_utils import (  # noqa: PLC0415
            ApatheticLogging_Internal_LoggingUtils,
        )

        level = ApatheticLogging_Internal_LoggingRoot.getEffectiveRootLevel()
        return ApatheticLogging_Internal_LoggingUtils.getLevelNameStr(level)

    @staticmethod
    def setRootLevel(  # noqa: PLR0912
        level: str | int,
        *,
        apply_to_children: bool = True,
        set_children_to_level: bool = True,
        root: logging.Logger | None = None,
    ) -> None:
        """Set the log level on the root logger and optionally on child loggers.

        This is the recommended way to set log levels in a CLI application,
        as it ensures all loggers (including those from libraries) use the
        same level. When propagation is enabled (default), child loggers
        inherit from root, so setting root level affects all loggers.

        Args:
            level: The log level to set, as a string name (case-insensitive)
                or integer value. Supports standard levels (DEBUG, INFO, etc.)
                and custom levels (TRACE, DETAIL, BRIEF, SILENT).
            apply_to_children: If True (default), also sets level on any child
                loggers that are not NOTSET. This handles loggers that were
                created before the root level was set. If False, only sets
                level on the root logger.
            set_children_to_level: If True (default), sets child loggers to
                the same level as root. If False, sets child loggers to NOTSET
                so they inherit from root. Only used when apply_to_children=True.
            root: The logger to use as the root. If None (default), uses the
                actual root logger (logging.getLogger(ROOT_LOGGER_KEY)).
                Can pass any logger to work on its children instead.

        Example:
            >>> from apathetic_logging import setRootLevel
            >>> # Set root level - all loggers inherit
            >>> setRootLevel("debug")
            >>> # Set root level and reset all child loggers to NOTSET
            >>> setRootLevel("info", set_children_to_level=False)
            >>> # Set level on a specific logger and its children
            >>> my_logger = getLogger("myapp")
            >>> setRootLevel("warning", root=my_logger)
        """
        from .constants import (  # noqa: PLC0415
            ApatheticLogging_Internal_Constants,
        )
        from .logging_utils import (  # noqa: PLC0415
            ApatheticLogging_Internal_LoggingUtils,
        )

        _logging_utils = ApatheticLogging_Internal_LoggingUtils
        _constants = ApatheticLogging_Internal_Constants

        # Resolve level string to integer if needed
        if isinstance(level, str):
            level_int = _logging_utils.getLevelNumber(level)
        else:
            level_int = level

        # Get root logger (or use provided one)
        # Note: logging.getLogger("") returns the root logger, but its .name is "root"
        # We need to check for both "" and "root" as root logger names
        if root is None:
            root_logger = logging.getLogger(_constants.ROOT_LOGGER_KEY)
        else:
            root_logger = root

        # Set level on root logger
        root_logger.setLevel(level_int)

        # Optionally apply to children
        if apply_to_children:
            root_name = root_logger.name
            # Find all child loggers
            # Children are loggers whose name starts with root_name + "."
            # (or any logger if root_name is "")
            for logger_name, logger in logging.Logger.manager.loggerDict.items():
                # Skip if not a Logger instance
                if not isinstance(logger, logging.Logger):
                    continue

                # Skip the root logger itself
                if logger is root_logger:
                    continue

                # Check if this is a child of root
                is_child = False
                # Root logger can have name "" or "root" depending on Python version
                root_names = {_constants.ROOT_LOGGER_KEY, _constants.ROOT_LOGGER_NAME}
                if root_name in root_names:
                    # Root logger - any logger with a name is a child
                    is_child = logger_name not in {
                        _constants.ROOT_LOGGER_KEY,
                        _constants.ROOT_LOGGER_NAME,
                    }
                else:
                    # Named root - child names start with root_name + "."
                    is_child = logger_name.startswith(root_name + ".")

                if is_child and logger.level != _constants.INHERIT_LEVEL:
                    # This child has an explicit level set
                    if set_children_to_level:
                        # Set child to same level as root
                        logger.setLevel(level_int)
                    else:
                        # Set child to INHERIT_LEVEL (i.e. NOTSET) so it
                        # inherits from root
                        logger.setLevel(_constants.INHERIT_LEVEL)

    @staticmethod
    def setRootLevelMinimum(level: str | int) -> None:
        """Set root logger level only if more verbose than current level.

        This is a convenience method that prevents downgrades from more verbose
        to less verbose levels.

        Args:
            level: The log level to potentially set, as a string name
                (case-insensitive) or integer value.

        Example:
            >>> setRootLevelMinimum("DEBUG")
            >>> # Root at DEBUG
            >>> setRootLevelMinimum("INFO")
            >>> # Still at DEBUG (more verbose is kept)

        See Also:
            setRootLevel() - Set level unconditionally
        """
        from .constants import (  # noqa: PLC0415
            ApatheticLogging_Internal_Constants,
        )
        from .logging_utils import (  # noqa: PLC0415
            ApatheticLogging_Internal_LoggingUtils,
        )

        _logging_utils = ApatheticLogging_Internal_LoggingUtils
        _constants = ApatheticLogging_Internal_Constants

        # Resolve level string to integer if needed
        if isinstance(level, str):
            level_int = _logging_utils.getLevelNumber(level)
        else:
            level_int = level

        # Get root logger
        root = logging.getLogger(_constants.ROOT_LOGGER_KEY)
        current_level = root.getEffectiveLevel()

        # Only set if new level is more verbose (lower numeric value)
        if level_int < current_level:
            root.setLevel(level_int)

    @staticmethod
    @contextmanager
    def useRootLevel(
        level: str | int,
        *,
        minimum: bool = False,
    ) -> Generator[None, None, None]:
        """Context manager to temporarily set root logger level.

        Sets the root logger to a specific level for the duration of the with block,
        then restores the previous level. Useful for temporarily increasing verbosity
        for debugging or testing.

        Args:
            level: The temporary log level to use, as a string name
                (case-insensitive) or integer value.
            minimum: If True, only applies the level if it's more verbose
                (lower numeric value) than the current effective level. If False
                (default), always sets the level. When minimum=True, the
                comparison is against the effective level (which considers parent
                inheritance, though root has no parent).

        Yields:
            None

        Example:
            >>> setRootLevel("INFO")
            >>> with useRootLevel("DEBUG"):
            ...     debug_logger.debug("This is logged at DEBUG")
            >>> # Back to INFO level

            >>> # Only debug if not already at DEBUG
            >>> with useRootLevel("DEBUG", minimum=True):
            ...     pass

        See Also:
            useRootLevelMinimum() - Convenience for useRootLevel(level, minimum=True)
            setRootLevel() - Permanently set level
        """
        from .constants import (  # noqa: PLC0415
            ApatheticLogging_Internal_Constants,
        )
        from .logging_utils import (  # noqa: PLC0415
            ApatheticLogging_Internal_LoggingUtils,
        )

        _constants = ApatheticLogging_Internal_Constants
        _logging_utils = ApatheticLogging_Internal_LoggingUtils

        # Resolve level string to integer if needed
        if isinstance(level, str):
            level_int = _logging_utils.getLevelNumber(level)
        else:
            level_int = level

        # Get root logger
        root = logging.getLogger(_constants.ROOT_LOGGER_KEY)
        old_level = root.level

        # Check minimum condition if requested
        if minimum:
            current_effective = root.getEffectiveLevel()
            # Only set if more verbose (lower numeric value)
            if level_int >= current_effective:
                # Not more verbose, don't change level
                yield
                return

        try:
            # Set temporary level
            root.setLevel(level_int)
            yield
        finally:
            # Restore original level
            root.setLevel(old_level)

    @staticmethod
    @contextmanager
    def useRootLevelMinimum(level: str | int) -> Generator[None, None, None]:
        """Context manager to temporarily set root level only if more verbose.

        Convenience context manager equivalent to useRootLevel(level, minimum=True).
        Only applies the level if it's more verbose than the current effective level.

        Args:
            level: The temporary log level to potentially use, as a string name
                (case-insensitive) or integer value.

        Yields:
            None

        Example:
            >>> with useRootLevelMinimum("DEBUG"):
            ...     # DEBUG level active only if not already more verbose
            ...     pass

        See Also:
            useRootLevel() - For unconditional temporary level change
        """
        with ApatheticLogging_Internal_LoggingRoot.useRootLevel(level, minimum=True):
            yield

    @staticmethod
    def isRootEnabledFor(level: str | int) -> bool:
        """Check if root logger would process messages at the given level.

        Returns True if the root logger's effective level would allow messages
        at the given level to be processed. Useful for conditional expensive
        operations that should only run if logging is enabled.

        Args:
            level: Log level to check, as a string name (case-insensitive)
                or integer value.

        Returns:
            True if messages at this level would be processed, False otherwise.

        Example:
            >>> setRootLevel("INFO")
            >>> isRootEnabledFor("DEBUG")
            False
            >>> isRootEnabledFor("INFO")
            True
            >>> isRootEnabledFor("WARNING")
            True

        See Also:
            getRootLevel() - Get current root level
        """
        from .constants import (  # noqa: PLC0415
            ApatheticLogging_Internal_Constants,
        )
        from .logging_utils import (  # noqa: PLC0415
            ApatheticLogging_Internal_LoggingUtils,
        )

        _constants = ApatheticLogging_Internal_Constants
        _logging_utils = ApatheticLogging_Internal_LoggingUtils

        # Resolve level string to integer if needed
        if isinstance(level, str):
            level_int = _logging_utils.getLevelNumber(level)
        else:
            level_int = level

        root = logging.getLogger(_constants.ROOT_LOGGER_KEY)
        return root.isEnabledFor(level_int)

    @staticmethod
    def logRootDynamic(
        level: str | int,
        msg: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Log a message to root logger with dynamically provided level.

        This allows logging with a level that is determined at runtime rather
        than compile time. Useful when the logging level comes from user input,
        configuration, or other dynamic sources.

        Args:
            level: Log level as string name (case-insensitive) or integer value.
            msg: The log message.
            *args: Arguments for message formatting (e.g., for % formatting).
            **kwargs: Additional keyword arguments for logging (exc_info,
                stack_info, etc.).

        Example:
            >>> level = "DEBUG"
            >>> logRootDynamic(level, "Message at %s level", level)
            >>> logRootDynamic(logging.DEBUG, "Direct integer level")

        See Also:
            getRootLogger() - Get root logger for standard logging methods
        """
        from .constants import (  # noqa: PLC0415
            ApatheticLogging_Internal_Constants,
        )
        from .logging_utils import (  # noqa: PLC0415
            ApatheticLogging_Internal_LoggingUtils,
        )

        _constants = ApatheticLogging_Internal_Constants
        _logging_utils = ApatheticLogging_Internal_LoggingUtils

        # Resolve level string to integer if needed
        if isinstance(level, str):
            level_int = _logging_utils.getLevelNumber(level)
        else:
            level_int = level

        root = logging.getLogger(_constants.ROOT_LOGGER_KEY)
        root.log(level_int, msg, *args, **kwargs)
