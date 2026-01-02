# src/apathetic_logging/registry.py
"""Registry functionality for Apathetic Logging."""

from __future__ import annotations

import logging
from typing import TypeVar

from .logging_utils import (
    ApatheticLogging_Internal_LoggingUtils,
)
from .registry_data import (
    ApatheticLogging_Internal_RegistryData,
)
from .safe_logging import (
    ApatheticLogging_Internal_SafeLogging,
)


class ApatheticLogging_Internal_Registry:  # noqa: N801  # pyright: ignore[reportUnusedClass]
    """Mixin class that provides registration methods.

    This class contains static methods for registering configuration values.
    When mixed into apathetic_logging, it provides registration methods for
    log level environment variables, default log level, logger name, and
    target Python version.

    Registry storage is provided by ``ApatheticLogging_Internal_RegistryData``.

    **Static Methods:**
    - ``registerDefaultLogLevel()``: Register the default log level
    - ``registerLogLevelEnvVars()``: Register environment variable names
    - ``registerLogger()``: Register a logger (public API)
    - ``registerTargetPythonVersion()``: Register target Python version
    - ``registerPropagate()``: Register propagate setting
    - ``registerCompatibilityMode()``: Register compatibility mode setting
    """

    _LoggerType = TypeVar("_LoggerType", bound=logging.Logger)

    @staticmethod
    def registerDefaultLogLevel(default_level: str | None) -> None:
        """Register the default log level to use when no other source is found.

        Args:
            default_level: Default log level name (e.g., "info", "warning").
                If None, returns immediately without making any changes.

        Example:
            >>> from apathetic_logging import ApatheticLogging
            >>> apathetic_logging.registerDefaultLogLevel("warning")
        """
        if default_level is None:
            return

        _registry_data = ApatheticLogging_Internal_RegistryData
        _safe_logging = ApatheticLogging_Internal_SafeLogging

        _registry_data.registered_internal_default_log_level = default_level
        _safe_logging.safeTrace(
            "registerDefaultLogLevel() called",
            f"default_level={default_level}",
        )

    @staticmethod
    def registerLogLevelEnvVars(env_vars: list[str] | None) -> None:
        """Register environment variable names to check for log level.

        The environment variables will be checked in order, and the first
        non-empty value found will be used.

        Args:
            env_vars: List of environment variable names to check
                (e.g., ["SERGER_LOG_LEVEL", "LOG_LEVEL"]).
                If None, returns immediately without making any changes.

        Example:
            >>> from apathetic_logging import ApatheticLogging
            >>> apathetic_logging.registerLogLevelEnvVars(
            ...     ["MYAPP_LOG_LEVEL", "LOG_LEVEL"]
            ... )
        """
        if env_vars is None:
            return

        _registry_data = ApatheticLogging_Internal_RegistryData
        _safe_logging = ApatheticLogging_Internal_SafeLogging

        _registry_data.registered_internal_log_level_env_vars = env_vars
        _safe_logging.safeTrace(
            "registerLogLevelEnvVars() called",
            f"env_vars={env_vars}",
        )

    @staticmethod
    def registerLogger(
        logger_name: str | None = None,
        logger_class: type[ApatheticLogging_Internal_Registry._LoggerType]
        | None = None,
        *,
        target_python_version: tuple[int, int] | None = None,
        log_level_env_vars: list[str] | None = None,
        default_log_level: str | None = None,
        propagate: bool | None = None,
        compat_mode: bool | None = None,
        replace_root: bool | None = None,
    ) -> None:
        """Register a logger for use by getLogger().

        This is the public API for registering a logger. It registers the logger
        name and extends the logging module with custom levels if needed.

        If logger_name is not provided, the top-level package is automatically
        extracted from the calling module's __package__ attribute.

        If logger_class is provided and has an ``extendLoggingModule()``
        method, it will be called to extend the logging module with custom
        levels and set the logger class. If logger_class is provided but does
        not have ``extendLoggingModule()``, ``logging.setLoggerClass()``
        will be called directly to set the logger class. If logger_class is not
        provided, nothing is done with the logger class (the default ``Logger``
        is already extended at import time).

        **Important**: If you're using a custom logger class that has
        ``extendLoggingModule()``, do not call ``logging.setLoggerClass()``
        directly. Instead, pass the class to ``registerLogger()`` and let
        ``extendLoggingModule()`` handle setting the logger class. This
        ensures consistent behavior and avoids class identity issues in
        stitched mode.

        Args:
            logger_name: The name of the logger to retrieve (e.g., "myapp").
                If None, extracts the top-level package from __package__.
            logger_class: Optional logger class to use. If provided and the class
                has an ``extendLoggingModule()`` method, it will be called.
                If the class doesn't have that method, ``logging.setLoggerClass()``
                will be called directly. If None, nothing is done (default Logger
                is already set up at import time).
            target_python_version: Optional target Python version (major, minor)
                tuple. If provided, sets the target Python version in the registry
                permanently. Defaults to None (no change).
            log_level_env_vars: Optional list of environment variable names to
                check for log level. If provided, sets the log level environment
                variables in the registry permanently. Defaults to None (no change).
            default_log_level: Optional default log level name. If provided, sets
                the default log level in the registry permanently. Defaults to None
                (no change).
            propagate: Optional propagate setting. If provided, sets the propagate
                value in the registry permanently. If None, uses registered propagate
                setting or falls back to DEFAULT_PROPAGATE from constants.py.
                Defaults to None (no change).
            compat_mode: Optional compatibility mode setting. If provided, sets
                the compatibility mode in the registry permanently. When True, restores
                stdlib-compatible behavior where possible (e.g., getLogger(None) returns
                root logger). If None, uses registered compatibility mode setting or
                defaults to False (improved behavior). Defaults to None (no change).
            replace_root: Optional setting for whether to replace root logger.
                If provided, passes this value to extendLoggingModule() when extending
                the logging module. If None, uses registry setting or constant default.
                Only used when logger_class has an extendLoggingModule() method.

        Example:
            >>> # Explicit registration with default Logger (already extended)
            >>> from apathetic_logging import registerLogger
            >>> registerLogger("myapp")

            >>> # Auto-infer from __package__
            >>> registerLogger()
            ...     # Uses top-level package from __package__

            >>> # Register with custom logger class (has extendLoggingModule)
            >>> from apathetic_logging import Logger
            >>> class AppLogger(Logger):
            ...     pass
            >>> # Don't call AppLogger.extendLoggingModule() or
            >>> # logging.setLoggerClass() directly - registerLogger() handles it
            >>> registerLogger("myapp", AppLogger)

            >>> # Register with any logger class (no extendLoggingModule)
            >>> import logging
            >>> class SimpleLogger(logging.Logger):
            ...     pass
            >>> registerLogger("myapp", SimpleLogger)  # Sets logger class directly
        """
        _registry = ApatheticLogging_Internal_Registry
        _registry_data = ApatheticLogging_Internal_RegistryData
        _logging_utils = ApatheticLogging_Internal_LoggingUtils
        _safe_logging = ApatheticLogging_Internal_SafeLogging

        # Handle convenience parameters that set registry values
        _registry.registerTargetPythonVersion(target_python_version)
        _registry.registerLogLevelEnvVars(log_level_env_vars)
        _registry.registerDefaultLogLevel(default_log_level)
        _registry.registerPropagate(propagate=propagate)
        _registry.registerCompatibilityMode(compat_mode=compat_mode)
        _registry.registerReplaceRootLogger(replace_root=replace_root)

        # Import Logger locally to avoid circular import

        # Track if name was auto-inferred
        was_explicit = logger_name is not None

        # Resolve logger name (with inference if needed)
        # skip_frames=1 because: registerLogger -> getDefaultLoggerName -> caller
        # check_registry=False because registerLogger() should actively determine
        # the name from the current context, not return an old registered name. This
        # allows re-inferring from __package__ if the package context has changed.
        # raise_on_error=True because registerLogger() requires a logger name.
        # register=True because registerLogger() should store the resolved name.
        resolved_name = _logging_utils.getDefaultLoggerName(
            logger_name,
            check_registry=False,
            skip_frames=1,
            raise_on_error=True,
            infer=True,
            register=True,
        )

        if logger_class is not None:
            # extendLoggingModule will call setLoggerClass for those that support it
            if hasattr(logger_class, "extendLoggingModule"):
                logger_class.extendLoggingModule(replace_root=replace_root)  # type: ignore[attr-defined]
            else:
                # stdlib unwrapped
                logging.setLoggerClass(logger_class)

        # registerLogger always stores the result (explicit or inferred)
        _registry_data.registered_internal_logger_name = resolved_name

        _safe_logging.safeTrace(
            "registerLogger() called",
            f"name={resolved_name}",
            f"auto_inferred={not was_explicit}",
            f"logger_class={logger_class.__name__ if logger_class else None}",
        )

    @staticmethod
    def registerTargetPythonVersion(version: tuple[int, int] | None) -> None:
        """Register the target Python version for compatibility checking.

        This sets the target Python version that will be used to validate
        function calls. If a function requires a Python version newer than
        the target version, it will raise a NotImplementedError even if
        the runtime version is sufficient.

        If not set, the library defaults to TARGET_PYTHON_VERSION (3, 10) from
        constants.py. This allows developers to catch version incompatibilities
        during development even when running on a newer Python version than
        their target.

        Args:
            version: Target Python version as (major, minor) tuple
                (e.g., (3, 10) or (3, 11)). If None, returns immediately
                without making any changes.

        Example:
            >>> from apathetic_logging import registerTargetPythonVersion
            >>> registerTargetPythonVersion((3, 10))
            >>> # Now functions requiring 3.11+ will raise if called

        Note:
            The runtime version is still checked as a safety net. If the
            runtime version is older than required, the function will still
            raise an error even if the target version is sufficient.
        """
        if version is None:
            return

        _registry_data = ApatheticLogging_Internal_RegistryData
        _safe_logging = ApatheticLogging_Internal_SafeLogging

        _registry_data.registered_internal_target_python_version = version
        _safe_logging.safeTrace(
            "registerTargetPythonVersion() called",
            f"version={version[0]}.{version[1]}",
        )

    @staticmethod
    def registerPropagate(*, propagate: bool | None) -> None:
        """Register the propagate setting for loggers.

        This sets the default propagate value that will be used when creating
        loggers. If not set, the library defaults to DEFAULT_PROPAGATE (True)
        from constants.py.

        When propagate is True, loggers propagate messages to parent loggers,
        allowing centralized control via root logger.

        Args:
            propagate: Propagate setting (True or False). If None, returns
                immediately without making any changes.

        Example:
            >>> from apathetic_logging import registerPropagate
            >>> registerPropagate(propagate=True)
            >>> # Now new loggers will propagate by default
        """
        if propagate is None:
            return

        _registry_data = ApatheticLogging_Internal_RegistryData
        _safe_logging = ApatheticLogging_Internal_SafeLogging

        _registry_data.registered_internal_propagate = propagate
        _safe_logging.safeTrace(
            "registerPropagate() called",
            f"propagate={propagate}",
        )

    @staticmethod
    def registerCompatibilityMode(*, compat_mode: bool | None) -> None:
        """Register the compatibility mode setting for stdlib drop-in replacement.

        This sets the compatibility mode that will be used when creating loggers.
        If not set, the library defaults to False (improved behavior).

        When compat_mode is True, restores stdlib-compatible behavior where
        possible (e.g., getLogger(None) returns root logger instead of auto-inferring).

        Args:
            compat_mode: Compatibility mode setting (True or False). If None,
                returns immediately without making any changes.

        Example:
            >>> from apathetic_logging import registerCompatibilityMode
            >>> registerCompatibilityMode(compat_mode=True)
            >>> # Now getLogger(None) returns root logger (stdlib behavior)
        """
        if compat_mode is None:
            return

        _registry_data = ApatheticLogging_Internal_RegistryData
        _safe_logging = ApatheticLogging_Internal_SafeLogging

        _registry_data.registered_internal_compatibility_mode = compat_mode
        _safe_logging.safeTrace(
            "registerCompatibilityMode() called",
            f"compat_mode={compat_mode}",
        )

    @staticmethod
    def registerReplaceRootLogger(*, replace_root: bool | None) -> None:
        """Register whether to replace root logger if it's not the correct type.

        This sets whether extendLoggingModule() should replace the root logger
        if it's not an instance of the apathetic logger class. If not set, the
        library defaults to DEFAULT_REPLACE_ROOT_LOGGER from constants.py
        (True by default - replace root logger to ensure it's an apathetic logger).

        When replace_root is False, extendLoggingModule() will not replace the
        root logger, allowing applications to use their own custom logger class
        for the root logger. This is useful when:
        - Using apathetic logging through a library (like utils) but wanting a
          different logger class for the root logger
        - Having your own custom logger class that inherits from logging.Logger
          and wanting to use it for the root logger

        Args:
            replace_root: Whether to replace root logger (True or False). If None,
                returns immediately without making any changes.

        Example:
            >>> from apathetic_logging import registerReplaceRootLogger
            >>> # Disable root logger replacement to use your own logger class
            >>> registerReplaceRootLogger(replace_root=False)
            >>> # Now extendLoggingModule() won't replace the root logger
        """
        if replace_root is None:
            return

        _registry_data = ApatheticLogging_Internal_RegistryData
        _safe_logging = ApatheticLogging_Internal_SafeLogging

        _registry_data.registered_internal_replace_root_logger = replace_root
        _safe_logging.safeTrace(
            "registerReplaceRootLogger() called",
            f"replace_root={replace_root}",
        )

    @staticmethod
    def registerPortHandlers(*, port_handlers: bool | None) -> None:
        """Register whether to port handlers when replacing a logger.

        This sets whether logger replacement should port handlers from the old
        logger to the new logger. If not set, the library defaults to
        DEFAULT_PORT_HANDLERS from constants.py (True by default - port handlers
        to preserve existing configuration).

        When port_handlers is True, handlers from the old logger are ported to
        the new logger. When False, the new logger manages its own handlers via
        manageHandlers() (may conflict with ported handlers).

        Args:
            port_handlers: Whether to port handlers (True or False). If None,
                returns immediately without making any changes.

        Example:
            >>> from apathetic_logging import registerPortHandlers
            >>> # Enable handler porting to preserve existing handlers
            >>> registerPortHandlers(port_handlers=True)
            >>> # Now logger replacement will port handlers
        """
        if port_handlers is None:
            return

        _registry_data = ApatheticLogging_Internal_RegistryData
        _safe_logging = ApatheticLogging_Internal_SafeLogging

        _registry_data.registered_internal_port_handlers = port_handlers
        _safe_logging.safeTrace(
            "registerPortHandlers() called",
            f"port_handlers={port_handlers}",
        )

    @staticmethod
    def registerPortLevel(*, port_level: bool | None) -> None:
        """Register whether to port level when replacing a logger.

        This sets whether logger replacement should port the log level from the
        old logger to the new logger. If not set, the library defaults to
        DEFAULT_PORT_LEVEL from constants.py (True by default - port level to
        preserve existing configuration).

        When port_level is True (default), the log level is ported from the old
        logger. When False, the new logger uses apathetic defaults:
        - Root logger: uses determineLogLevel() to get a sensible default
        - Leaf loggers: use INHERIT_LEVEL (NOTSET) to inherit from parent
        Note: User-provided level parameters in getLogger/getLoggerOfType take
        precedence over ported level.

        Args:
            port_level: Whether to port level (True or False). If None,
                returns immediately without making any changes.

        Example:
            >>> from apathetic_logging import registerPortLevel
            >>> # Enable level porting to preserve existing level
            >>> registerPortLevel(port_level=True)
            >>> # Now logger replacement will port level
        """
        if port_level is None:
            return

        _registry_data = ApatheticLogging_Internal_RegistryData
        _safe_logging = ApatheticLogging_Internal_SafeLogging

        _registry_data.registered_internal_port_level = port_level
        _safe_logging.safeTrace(
            "registerPortLevel() called",
            f"port_level={port_level}",
        )

    @staticmethod
    def getLogLevelEnvVars() -> list[str]:
        """Get the environment variable names to check for log level.

        Returns the registered environment variable names, or the default
        environment variables if none are registered.

        Returns:
            List of environment variable names to check for log level.
            Defaults to ["LOG_LEVEL"] if not registered.

        Example:
            >>> from apathetic_logging import getLogLevelEnvVars
            >>> env_vars = getLogLevelEnvVars()
            >>> print(env_vars)
            ["LOG_LEVEL"]
        """
        from .constants import (  # noqa: PLC0415
            ApatheticLogging_Internal_Constants,
        )
        from .registry_data import (  # noqa: PLC0415
            ApatheticLogging_Internal_RegistryData,
        )

        _constants = ApatheticLogging_Internal_Constants
        _registry_data = ApatheticLogging_Internal_RegistryData

        return (
            _registry_data.registered_internal_log_level_env_vars
            or _constants.DEFAULT_APATHETIC_LOG_LEVEL_ENV_VARS
        )

    @staticmethod
    def getDefaultLogLevel() -> str:
        """Get the default log level.

        Returns the registered default log level, or the module default
        if none is registered.

        Returns:
            Default log level name (e.g., "detail", "info").
            Defaults to "detail" if not registered.

        Example:
            >>> from apathetic_logging import getDefaultLogLevel
            >>> level = getDefaultLogLevel()
            >>> print(level)
            "detail"
        """
        from .constants import (  # noqa: PLC0415
            ApatheticLogging_Internal_Constants,
        )
        from .registry_data import (  # noqa: PLC0415
            ApatheticLogging_Internal_RegistryData,
        )

        _constants = ApatheticLogging_Internal_Constants
        _registry_data = ApatheticLogging_Internal_RegistryData

        return (
            _registry_data.registered_internal_default_log_level
            or _constants.DEFAULT_APATHETIC_LOG_LEVEL
        )

    @staticmethod
    def getRegisteredLoggerName() -> str | None:
        """Get the registered logger name.

        Returns the registered logger name, or None if no logger name
        has been registered. Unlike getDefaultLoggerName(), this does not
        perform inference - it only returns the explicitly registered value.

        Returns:
            Registered logger name, or None if not registered.

        Example:
            >>> from apathetic_logging import getRegisteredLoggerName
            >>> name = getRegisteredLoggerName()
            >>> if name is None:
            ...     print("No logger name registered")
        """
        from .registry_data import (  # noqa: PLC0415
            ApatheticLogging_Internal_RegistryData,
        )

        _registry_data = ApatheticLogging_Internal_RegistryData

        return _registry_data.registered_internal_logger_name

    @staticmethod
    def getTargetPythonVersion() -> tuple[int, int] | None:
        """Get the target Python version.

        Returns the registered target Python version, or the minimum
        supported version if none is registered.

        Returns:
            Target Python version as (major, minor) tuple, or None if
            no version is registered and TARGET_PYTHON_VERSION is None
            (checks disabled).

        Example:
            >>> from apathetic_logging import getTargetPythonVersion
            >>> version = getTargetPythonVersion()
            >>> print(version)
            (3, 10)  # or None if checks are disabled
        """
        from .constants import (  # noqa: PLC0415
            ApatheticLogging_Internal_Constants,
        )
        from .registry_data import (  # noqa: PLC0415
            ApatheticLogging_Internal_RegistryData,
        )

        _constants = ApatheticLogging_Internal_Constants
        _registry_data = ApatheticLogging_Internal_RegistryData

        return (
            _registry_data.registered_internal_target_python_version
            or _constants.TARGET_PYTHON_VERSION
        )

    @staticmethod
    def getDefaultPropagate() -> bool:
        """Get the default propagate setting.

        Returns the registered propagate setting, or the module default
        (DEFAULT_PROPAGATE) from constants.py if not registered.

        Returns:
            Default propagate setting (True or False).

        Example:
            >>> from apathetic_logging import getDefaultPropagate
            >>> propagate = getDefaultPropagate()
            >>> print(propagate)
            True
        """
        from .constants import (  # noqa: PLC0415
            ApatheticLogging_Internal_Constants,
        )
        from .registry_data import (  # noqa: PLC0415
            ApatheticLogging_Internal_RegistryData,
        )

        _constants = ApatheticLogging_Internal_Constants
        _registry_data = ApatheticLogging_Internal_RegistryData

        return (
            _registry_data.registered_internal_propagate
            if _registry_data.registered_internal_propagate is not None
            else _constants.DEFAULT_PROPAGATE
        )

    @staticmethod
    def getCompatibilityMode() -> bool:
        """Get the compatibility mode setting.

        Returns the registered compatibility mode setting, or False (improved
        behavior) if not registered.

        Returns:
            Compatibility mode setting (True or False).
            Defaults to False if not registered.

        Example:
            >>> from apathetic_logging import getCompatibilityMode
            >>> compat_mode = getCompatibilityMode()
            >>> print(compat_mode)
            False
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
