# src/apathetic_logging/logging_std_camel.py
"""Camel case convenience functions for standard logging module.

This module provides direct wrappers for stdlib logging.* namespace functions
with no additional logic or "smarts". These are simple pass-through functions
that maintain camelCase naming for compatibility.

For utility functions with additional logic (e.g., setRootLevel), see
logging_utils.py instead.

Docstrings are adapted from the standard library logging module documentation
licensed under the Python Software Foundation License Version 2.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from types import FrameType
from typing import Any

from .logging_utils import (
    ApatheticLogging_Internal_LoggingUtils,
)


class ApatheticLogging_Internal_StdCamelCase:  # noqa: N801  # pyright: ignore[reportUnusedClass]
    """Mixin class that provides camelCase convenience functions for logging.*.

    This class contains camelCase wrapper functions for standard library
    `logging.*` functions that use camelCase naming. These wrappers provide
    direct compatibility with the standard logging module interface while
    maintaining full compatibility with the underlying logging module functions.

    When mixed into apathetic_logging, it provides camelCase functions
    that match the standard logging module functions (e.g., `basicConfig`,
    `addLevelName`, `setLoggerClass`, `getLogger`).
    """

    # --- Configuration Functions ---

    @staticmethod
    def basicConfig(*args: Any, **kwargs: Any) -> None:
        """Do basic configuration for the logging system.

        This function does nothing if the root logger already has handlers
        configured, unless the keyword argument *force* is set to ``True``.
        It is a convenience method intended for use by simple scripts
        to do one-shot configuration of the logging package.

        The default behaviour is to create a StreamHandler which writes to
        sys.stderr, set a formatter using the BASIC_FORMAT format string, and
        add the handler to the root logger.

        A number of optional keyword arguments may be specified, which can alter
        the default behaviour.

        Wrapper for logging.basicConfig with camelCase naming.

        https://docs.python.org/3.10/library/logging.html#logging.basicConfig
        """
        logging.basicConfig(*args, **kwargs)

    @staticmethod
    def captureWarnings(
        capture: bool,  # noqa: FBT001
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Redirect warnings to the logging package.

        If capture is true, redirect all warnings to the logging package.
        If capture is False, ensure that warnings are not redirected to logging
        but to their original destinations.

        Wrapper for logging.captureWarnings with camelCase naming.

        https://docs.python.org/3.10/library/logging.html#logging.captureWarnings
        """
        logging.captureWarnings(capture, *args, **kwargs)

    @staticmethod
    def shutdown(*args: Any, **kwargs: Any) -> None:
        """Perform any cleanup actions in the logging system.

        Perform any cleanup actions in the logging system (e.g. flushing
        buffers). Should be called at application exit.

        Wrapper for logging.shutdown with camelCase naming.

        https://docs.python.org/3.10/library/logging.html#logging.shutdown
        """
        logging.shutdown(*args, **kwargs)

    # --- Level Management Functions ---

    @staticmethod
    def addLevelName(level: int, level_name: str, *args: Any, **kwargs: Any) -> None:
        """Associate a level name with a numeric level.

        Associate 'level_name' with 'level'. This is used when converting
        levels to text during message formatting.

        Wrapper for logging.addLevelName with camelCase naming.

        https://docs.python.org/3.10/library/logging.html#logging.addLevelName
        """
        logging.addLevelName(level, level_name, *args, **kwargs)

    @staticmethod
    def getLevelName(level: int, *args: Any, **kwargs: Any) -> str | int:
        """Return the textual or numeric representation of a logging level.

        If the level is one of the predefined levels (CRITICAL, ERROR, WARNING,
        INFO, DEBUG) then you get the corresponding string. If you have
        associated levels with names using addLevelName then the name you have
        associated with 'level' is returned.

        If a numeric value corresponding to one of the defined levels is passed
        in, the corresponding string representation is returned.

        If a string representation of the level is passed in, the corresponding
        numeric value is returned.

        If no matching numeric or string value is passed in, the string
        'Level %s' % level is returned.

        Wrapper for logging.getLevelName with camelCase naming.

        https://docs.python.org/3.10/library/logging.html#logging.getLevelName
        """
        return logging.getLevelName(level, *args, **kwargs)

    @staticmethod
    def getLevelNamesMapping(*args: Any, **kwargs: Any) -> dict[int, str]:
        """Return a mapping of all level names to their numeric values.

        **Requires Python 3.11+**

        Wrapper for logging.getLevelNamesMapping with camelCase naming.

        https://docs.python.org/3.11/library/logging.html#logging.getLevelNamesMapping
        """
        _logging_utils = ApatheticLogging_Internal_LoggingUtils
        _logging_utils.checkPythonVersionRequirement((3, 11), "getLevelNamesMapping")
        return logging.getLevelNamesMapping(*args, **kwargs)  # type: ignore[attr-defined,no-any-return]

    @staticmethod
    def disable(level: int = 50, *args: Any, **kwargs: Any) -> None:
        """Disable all logging calls of severity 'level' and below.

        Wrapper for logging.disable with camelCase naming.

        https://docs.python.org/3.10/library/logging.html#logging.disable
        """
        logging.disable(level, *args, **kwargs)

    # --- Logger Management Functions ---

    @staticmethod
    def getLogger(
        name: str | None = None, *_args: Any, **_kwargs: Any
    ) -> logging.Logger:
        """Return a logger with the specified name, creating it if necessary.

        If no name is specified, return the root logger.

        Returns an logging.Logger instance.

        Wrapper for logging.getLogger with camelCase naming.

        https://docs.python.org/3.10/library/logging.html#logging.getLogger
        """
        return logging.getLogger(name)

    @staticmethod
    def getLoggerClass(*args: Any, **kwargs: Any) -> type[logging.Logger]:
        """Return the class to be used when instantiating a logger.

        Wrapper for logging.getLoggerClass with camelCase naming.

        https://docs.python.org/3.10/library/logging.html#logging.getLoggerClass
        """
        return logging.getLoggerClass(*args, **kwargs)

    @staticmethod
    def setLoggerClass(klass: type[logging.Logger], *args: Any, **kwargs: Any) -> None:
        """Set the class to be used when instantiating a logger.

        The class should define __init__() such that only a name argument is
        required, and the __init__() should call Logger.__init__().

        Args:
            klass (logger class): The logger class to use.
            *args: Additional positional arguments (for future-proofing).
            **kwargs: Additional keyword arguments (for future-proofing).

        Wrapper for logging.setLoggerClass with camelCase naming.

        https://docs.python.org/3.10/library/logging.html#logging.setLoggerClass
        """
        logging.setLoggerClass(klass, *args, **kwargs)

    # --- Handler Management Functions ---

    @staticmethod
    def getHandlerByName(
        name: str, *args: Any, **kwargs: Any
    ) -> logging.Handler | None:
        """Get a handler with the specified name, or None if there isn't one.

        **Requires Python 3.12+**

        Wrapper for logging.getHandlerByName with camelCase naming.

        https://docs.python.org/3.12/library/logging.html#logging.getHandlerByName
        """
        _logging_utils = ApatheticLogging_Internal_LoggingUtils
        _logging_utils.checkPythonVersionRequirement((3, 12), "getHandlerByName")
        return logging.getHandlerByName(name, *args, **kwargs)  # type: ignore[attr-defined,no-any-return]

    @staticmethod
    def getHandlerNames(*args: Any, **kwargs: Any) -> list[str]:
        """Return all known handler names as an immutable set.

        **Requires Python 3.12+**

        Wrapper for logging.getHandlerNames with camelCase naming.

        https://docs.python.org/3.12/library/logging.html#logging.getHandlerNames
        """
        _logging_utils = ApatheticLogging_Internal_LoggingUtils
        _logging_utils.checkPythonVersionRequirement((3, 12), "getHandlerNames")
        return logging.getHandlerNames(*args, **kwargs)  # type: ignore[attr-defined,no-any-return]

    # --- Factory Functions ---

    @staticmethod
    def getLogRecordFactory(
        *args: Any, **kwargs: Any
    ) -> Callable[..., logging.LogRecord]:
        """Return the factory to be used when instantiating a log record.

        Wrapper for logging.getLogRecordFactory with camelCase naming.

        https://docs.python.org/3.10/library/logging.html#logging.getLogRecordFactory
        """
        return logging.getLogRecordFactory(*args, **kwargs)

    @staticmethod
    def setLogRecordFactory(
        factory: Callable[..., logging.LogRecord], *args: Any, **kwargs: Any
    ) -> None:
        """Set the factory to be used when instantiating a log record.

        :param factory: A callable which will be called to instantiate
        a log record.

        Wrapper for logging.setLogRecordFactory with camelCase naming.

        https://docs.python.org/3.10/library/logging.html#logging.setLogRecordFactory
        """
        logging.setLogRecordFactory(factory, *args, **kwargs)

    @staticmethod
    def makeLogRecord(
        dict: dict[str, Any],  # noqa: A002  # Required to match stdlib logging.makeLogRecord signature
        *args: Any,
        **kwargs: Any,
    ) -> logging.LogRecord:
        """Make a LogRecord whose attributes are defined by a dictionary.

        This function is useful for converting a logging event received over
        a socket connection (which is sent as a dictionary) into a LogRecord
        instance.

        Wrapper for logging.makeLogRecord with camelCase naming.

        https://docs.python.org/3.10/library/logging.html#logging.makeLogRecord
        """
        return logging.makeLogRecord(dict, *args, **kwargs)

    # --- Logging Functions ---

    @staticmethod
    def critical(msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a message with severity 'CRITICAL' on the root logger.

        If the logger has no handlers, call basicConfig() to add a console
        handler with a pre-defined format.

        Wrapper for logging.critical with camelCase naming.

        https://docs.python.org/3.10/library/logging.html#logging.critical
        """
        logging.critical(msg, *args, **kwargs)  # noqa: LOG015

    @staticmethod
    def debug(msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a message with severity 'DEBUG' on the root logger.

        If the logger has no handlers, call basicConfig() to add a console
        handler with a pre-defined format.

        Wrapper for logging.debug with camelCase naming.

        https://docs.python.org/3.10/library/logging.html#logging.debug
        """
        logging.debug(msg, *args, **kwargs)  # noqa: LOG015

    @staticmethod
    def error(msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a message with severity 'ERROR' on the root logger.

        If the logger has no handlers, call basicConfig() to add a console
        handler with a pre-defined format.

        Wrapper for logging.error with camelCase naming.

        https://docs.python.org/3.10/library/logging.html#logging.error
        """
        logging.error(msg, *args, **kwargs)  # noqa: LOG015

    @staticmethod
    def exception(msg: str, *args: Any, exc_info: bool = True, **kwargs: Any) -> None:
        """Log a message with severity 'ERROR' on the root logger, with exception info.

        If the logger has no handlers, basicConfig() is called to add a console
        handler with a pre-defined format.

        Wrapper for logging.exception with camelCase naming.

        https://docs.python.org/3.10/library/logging.html#logging.exception
        """
        logging.exception(msg, *args, exc_info=exc_info, **kwargs)  # noqa: LOG015

    @staticmethod
    def fatal(msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a message with severity 'CRITICAL' on the root logger.

        Don't use this function, use critical() instead.

        Wrapper for logging.fatal with camelCase naming.

        https://docs.python.org/3.10/library/logging.html#logging.fatal
        """
        logging.fatal(msg, *args, **kwargs)

    @staticmethod
    def info(msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a message with severity 'INFO' on the root logger.

        If the logger has no handlers, call basicConfig() to add a console
        handler with a pre-defined format.

        Wrapper for logging.info with camelCase naming.

        https://docs.python.org/3.10/library/logging.html#logging.info
        """
        logging.info(msg, *args, **kwargs)  # noqa: LOG015

    @staticmethod
    def log(level: int, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log 'msg % args' with the integer severity 'level' on the root logger.

        If the logger has no handlers, call basicConfig() to add a console
        handler with a pre-defined format.

        Wrapper for logging.log with camelCase naming.

        https://docs.python.org/3.10/library/logging.html#logging.log
        """
        logging.log(level, msg, *args, **kwargs)  # noqa: LOG015

    @staticmethod
    def warn(msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a message with severity 'WARNING' on the root logger.

        If the logger has no handlers, call basicConfig() to add a console
        handler with a pre-defined format.

        Wrapper for logging.warn with camelCase naming.

        https://docs.python.org/3.10/library/logging.html#logging.warn
        """
        logging.warning(msg, *args, **kwargs)  # noqa: LOG015

    @staticmethod
    def warning(msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a message with severity 'WARNING' on the root logger.

        If the logger has no handlers, call basicConfig() to add a console
        handler with a pre-defined format.

        Wrapper for logging.warning with camelCase naming.

        https://docs.python.org/3.10/library/logging.html#logging.warning
        """
        logging.warning(msg, *args, **kwargs)  # noqa: LOG015

    # --- Utility Functions ---

    @staticmethod
    def currentframe(*args: Any, **kwargs: Any) -> FrameType | None:
        """Return the frame object for the caller's stack frame.

        Wrapper for logging.currentframe with camelCase naming.

        https://docs.python.org/3.10/library/logging.html#logging.currentframe
        """
        return logging.currentframe(*args, **kwargs)
