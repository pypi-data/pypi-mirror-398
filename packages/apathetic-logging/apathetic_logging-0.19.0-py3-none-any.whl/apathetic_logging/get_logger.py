# src/apathetic_logging/get_logger.py
"""GetLogger functionality for Apathetic Logging.

Docstrings are adapted from the standard library logging module documentation
licensed under the Python Software Foundation License Version 2.
"""

from __future__ import annotations

import logging
from typing import Any, TypeVar, cast

from .logger_namespace import (
    ApatheticLogging_Internal_Logger,
)
from .logging_utils import (
    ApatheticLogging_Internal_LoggingUtils,
)


class ApatheticLogging_Internal_GetLogger:  # noqa: N801  # pyright: ignore[reportUnusedClass]
    """Mixin class that provides the getLogger static method.

    This class contains the getLogger implementation as a static method.
    When mixed into apathetic_logging, it provides apathetic_logging.getLogger.
    """

    _LoggerType = TypeVar("_LoggerType", bound=logging.Logger)

    @staticmethod
    def _setLoggerClassTemporarily(
        klass: type[ApatheticLogging_Internal_GetLogger._LoggerType],
        name: str,
    ) -> ApatheticLogging_Internal_GetLogger._LoggerType:
        """Temporarily set the logger class, get/create a logger, then restore.

        This is an internal helper function used by getLoggerOfType to create
        a logger of a specific type when one doesn't already exist. It temporarily
        sets the logger class to the desired type, gets or creates the logger,
        then restores the original logger class.

        This function is mostly for internal use by the library. If you need
        a logger of a specific type, use getLoggerOfType instead, which provides
        all the conveniences (name inference, registry checking, etc.).

        Args:
            klass (logger class): The desired logger class type.
            name: The name of the logger to get.

        Returns:
            A logger instance of the specified type.
        """
        # stdlib unwrapped
        original_class = logging.getLoggerClass()
        logging.setLoggerClass(klass)
        # avoid circular dependency by using logging.getLogger directly
        logger = logging.getLogger(name)
        logging.setLoggerClass(original_class)
        typed_logger = cast("ApatheticLogging_Internal_GetLogger._LoggerType", logger)
        return typed_logger

    @staticmethod
    def _getOrCreateLoggerOfType(
        register_name: str,
        class_type: type[ApatheticLogging_Internal_GetLogger._LoggerType],
        *args: Any,
        **kwargs: Any,
    ) -> ApatheticLogging_Internal_GetLogger._LoggerType:
        """Get or create a logger of the specified type.

        Checks if a logger with the given name exists. If it exists but is not
        of the correct type, removes it and creates a new one. If it doesn't
        exist, creates a new logger of the specified type.

        Args:
            register_name: The name of the logger to get or create.
            class_type: The logger class type to use.
            *args: Additional positional arguments to pass to logging.getLogger.
            **kwargs: Additional keyword arguments to pass to logging.getLogger.

        Returns:
            A logger instance of the specified type.
        """
        _logging_utils = ApatheticLogging_Internal_LoggingUtils

        logger: logging.Logger | None = None
        old_logger: logging.Logger | None = None
        registered = _logging_utils.hasLogger(register_name)
        if registered:
            logger = logging.getLogger(register_name, *args, **kwargs)
            if not isinstance(logger, class_type):
                # Save reference to old logger before removing it
                old_logger = logger
                _logging_utils.removeLogger(register_name)
                registered = False
        if not registered:  # may have changed above
            # Save the parent that Python's logging module assigned before creating
            # logger. This is important because when we create a new logger, Python's
            # logging module might assign it a parent (e.g., old root logger or
            # intermediate logger)
            from .constants import (  # noqa: PLC0415
                ApatheticLogging_Internal_Constants,
            )

            _constants = ApatheticLogging_Internal_Constants

            # Get the parent that would be assigned by Python's logging module
            # We do this by temporarily creating the logger to see what parent it gets
            # But we can't do that without side effects, so we'll check after creation
            logger = ApatheticLogging_Internal_GetLogger._setLoggerClassTemporarily(
                class_type, register_name
            )

            # Save the parent that was assigned
            old_parent = logger.parent

            # Port state from old logger if we replaced an existing logger
            # (also reconnects child loggers internally)
            if old_logger is not None:
                # Port state from old logger, but user-provided kwargs take precedence
                # Check if level is explicitly provided in kwargs - if so, don't port
                # level (user's level will be applied later in getLoggerOfType)
                user_provided_level = kwargs.get("level")
                # Only port if user didn't provide level
                port_level = user_provided_level is None
                _logging_utils.portLoggerState(
                    old_logger,
                    logger,
                    port_handlers=None,  # Use default (True) - port handlers
                    port_level=port_level,  # Port level only if user didn't provide one
                )

            # Fix parent if it points to old root logger
            # Only fix if this is not the root logger itself
            if logger.name not in {
                _constants.ROOT_LOGGER_KEY,
                _constants.ROOT_LOGGER_NAME,
            }:
                # Check if old parent was the old root logger (has no parent itself)
                # Root logger is the only logger that has no parent
                if old_parent is not None:
                    # Check if old_parent might be the old root logger
                    # Root logger has no parent, and its name is "" or "root"
                    old_parent_might_be_old_root = (
                        old_parent.name
                        in {
                            _constants.ROOT_LOGGER_KEY,
                            _constants.ROOT_LOGGER_NAME,
                        }
                        and old_parent.parent is None
                    )

                    if old_parent_might_be_old_root:
                        # Get current root logger to check if it's different
                        # Only call logging.getLogger() when we actually need to fix
                        current_root = logging.getLogger(_constants.ROOT_LOGGER_KEY)
                        if old_parent is not current_root:
                            # Old parent was the old root logger - set to new root
                            logger.parent = current_root
                    # else: old parent was an intermediate logger - keep it
                    # (preserve hierarchy)
                else:
                    # No old parent (shouldn't happen for non-root loggers, but be safe)
                    # Get current root logger and set as parent
                    current_root = logging.getLogger(_constants.ROOT_LOGGER_KEY)
                    logger.parent = current_root

        typed_logger = cast("ApatheticLogging_Internal_GetLogger._LoggerType", logger)
        return typed_logger

    @staticmethod
    def _applyPropagateSetting(logger: logging.Logger) -> None:
        """Apply propagate setting to a logger from registry or default.

        This method implements the second phase of the two-phase propagate
        initialization pattern. It is called automatically by getLoggerOfType()
        after logger creation.

        **Contract with Logger.__init__:** Only applies the registry/default
        propagate value if the logger's _propagate_explicit flag is False,
        indicating that the user did not explicitly provide a propagate value
        in Logger.__init__(). This ensures that explicit user settings take
        precedence over registry/default values.

        If the logger does not have setPropagate() (e.g., standard logging.Logger),
        the propagate attribute is set directly.

        Args:
            logger: The logger instance to apply the propagate setting to.
        """
        from .registry import (  # noqa: PLC0415
            ApatheticLogging_Internal_Registry,
        )

        # Only set if not already explicitly set in __init__
        if not getattr(logger, "_propagate_explicit", False):
            # Use getDefaultPropagate() to resolve registry/default value
            propagate_value = ApatheticLogging_Internal_Registry.getDefaultPropagate()

            # Use setPropagate if available (apathetic logger), otherwise set directly
            if hasattr(logger, "setPropagate"):
                logger.setPropagate(propagate_value)  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]
            else:
                logger.propagate = propagate_value

    @staticmethod
    def getLogger(
        name: str | None = None,
        *args: Any,
        level: str | int | None = None,
        minimum: bool | None = None,
        extend: bool | None = None,
        replace_root: bool | None = None,
        **kwargs: Any,
    ) -> ApatheticLogging_Internal_Logger.Logger:
        """Return a logger with the specified name, creating it if necessary.

        Changes:
        - When name is None, infers the name automatically from
          the calling module's __package__ attribute by examining the call stack
          (using skip_frames=2 to correctly identify the caller)
          instead of returning the root logger.
        - When name is an empty string (""), returns the root logger
          as usual, matching standard library behavior.
        - Returns an apathetic_logging.Logger instance instead of
          the standard logging.Logger.

        Args:
            name: The name of the logger to get. If None, the logger name
                will be auto-inferred from the calling module's __package__.
                If an empty string (""), returns the root logger.
            *args: Additional positional arguments (for future-proofing)
            level: Log level to set on the logger. Accepts both string
                names (case-insensitive) and numeric values. Level 0 or
                INHERIT_LEVEL (i.e. NOTSET) allows inheritance from parent logger.
                - If not provided: defaults to INHERIT_LEVEL (inherits from root)
                - If None: auto-resolves via determineLogLevel()
                - If provided (str/int): sets the logger's level to this value
            minimum: If True, only set the level if it's more verbose (lower
                numeric value) than the current level. This prevents downgrading
                from a more verbose level (e.g., TRACE) to a less verbose one
                (e.g., DEBUG). If None, defaults to False. Only used when
                `level` is provided.
            extend: If True (default), extend the logging module.
            replace_root: Whether to replace the root logger if it's not the correct
                type. If None (default), uses registry setting or constant default.
                Only used when extend=True.
            **kwargs: Additional keyword arguments (for future-proofing)

        Returns:
            A logger of type ApatheticLogging_Internal_Logger.Logger.

        Wrapper for logging.getLogger.

        https://docs.python.org/3.10/library/logging.html#logging.getLogger
        """
        _get_logger = ApatheticLogging_Internal_GetLogger
        _logger = ApatheticLogging_Internal_Logger
        skip_frames = 2
        result = _get_logger.getLoggerOfType(
            name,
            _logger.Logger,
            skip_frames,
            *args,
            level=level,
            minimum=minimum,
            extend=extend,
            replace_root=replace_root,
            **kwargs,
        )
        return cast("ApatheticLogging_Internal_Logger.Logger", result)  # type: ignore[redundant-cast]

    @staticmethod
    def getLoggerOfType(
        name: str | None,
        class_type: type[ApatheticLogging_Internal_GetLogger._LoggerType],
        skip_frames: int = 1,
        *args: Any,
        level: str | int | None = None,
        minimum: bool | None = None,
        extend: bool | None = True,
        replace_root: bool | None = None,
        **kwargs: Any,
    ) -> ApatheticLogging_Internal_GetLogger._LoggerType:
        """Get a logger of the specified type, creating it if necessary.

        Changes:
        - When name is None, infers the name automatically from
          the calling module's __package__ attribute by examining the call stack
          (using skip_frames to correctly identify the caller)
          instead of returning the root logger.
        - When name is an empty string (""), returns the root logger
          as usual, matching standard library behavior.
        - Returns a class_type instance instead of
          the standard logging.Logger.

        Args:
            name: The name of the logger to get. If None, the logger name
                will be auto-inferred from the calling module's __package__.
                If an empty string (""), returns the root logger.
            class_type: The logger class type to use.
            skip_frames: Number of frames to skip when inferring logger name.
                Prefer using as a keyword argument (e.g., skip_frames=2) for clarity.
            *args: Additional positional arguments (for future-proofing)
            level: Exact log level to set on the logger. Accepts both string
                names (case-insensitive) and numeric values. Level 0 or
                INHERIT_LEVEL (i.e. NOTSET) allows inheritance from parent
                logger. If provided, sets the logger's level to this value.
                Defaults to None.
            minimum: If True, only set the level if it's more verbose (lower
                numeric value) than the current level. This prevents downgrading
                from a more verbose level (e.g., TRACE) to a less verbose one
                (e.g., DEBUG). If None, defaults to False. Only used when
                `level` is provided.
            extend: If True (default), extend the logging module.
            replace_root: Whether to replace the root logger if it's not the correct
                type. If None (default), uses registry setting or constant default.
                Only used when extend=True.
            **kwargs: Additional keyword arguments (for future-proofing)

        Returns:
            A logger instance of the specified type.

        Wrapper for logging.getLogger.

        https://docs.python.org/3.10/library/logging.html#logging.getLogger
        """
        _logging_utils = ApatheticLogging_Internal_LoggingUtils

        # Check compatibility mode for getLogger(None) behavior
        from .registry_data import (  # noqa: PLC0415
            ApatheticLogging_Internal_RegistryData,
        )

        _registry_data = ApatheticLogging_Internal_RegistryData
        compatibility_mode = (
            _registry_data.registered_internal_compatibility_mode
            if _registry_data.registered_internal_compatibility_mode is not None
            else False
        )

        # In compatibility mode, getLogger(None) returns root logger (stdlib behavior)
        if name is None and compatibility_mode:
            from .constants import (  # noqa: PLC0415
                ApatheticLogging_Internal_Constants,
            )

            register_name: str = ApatheticLogging_Internal_Constants.ROOT_LOGGER_KEY
        else:
            # Resolve logger name (with inference if needed)
            # Note: Empty string ("") is a special case - getDefaultLoggerName
            # returns it as-is (root logger, matching stdlib behavior). This is
            # handled by the
            # early return in getDefaultLoggerName when logger_name is not None.
            # skip_frames+1 because: getLoggerOfType -> getDefaultLoggerName -> caller
            # check_registry=True because getLogger() should use a previously registered
            # name if available, which is the expected behavior for "get" operations.
            # raise_on_error=True because getLogger() requires a logger name.
            # infer=True and register=True - getLogger() infers and stores (matches old
            # resolveLoggerName behavior where inferred names were automatically stored)
            register_name_raw = _logging_utils.getDefaultLoggerName(
                name,
                check_registry=True,
                skip_frames=skip_frames + 1,
                raise_on_error=True,
                infer=True,
                register=True,
            )
            # With raise_on_error=True, register_name is guaranteed to be str, not None
            register_name = register_name_raw  # type: ignore[assignment]

        # extend logging module
        if extend and hasattr(class_type, "extendLoggingModule"):
            class_type.extendLoggingModule(replace_root=replace_root)  # type: ignore[attr-defined]

        # Get or create logger of the correct type
        logger = ApatheticLogging_Internal_GetLogger._getOrCreateLoggerOfType(
            register_name, class_type, *args, **kwargs
        )

        # Apply log level settings
        if level is not None:
            logger.setLevel(
                level,
                minimum=minimum,  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue]
            )

        # Apply propagate setting from registry or default
        ApatheticLogging_Internal_GetLogger._applyPropagateSetting(logger)

        return logger
