# src/apathetic_logging/logging_levels.py
"""Custom log level functions for Apathetic Logging.

This module provides convenience functions for custom log levels (TEST, TRACE, DETAIL,
BRIEF) that don't exist in the standard library. These functions log
to the root logger and ensure the logging module is extended with custom levels.
"""

from __future__ import annotations

from typing import Any

from .constants import (
    ApatheticLogging_Internal_Constants,
)
from .get_logger import (
    ApatheticLogging_Internal_GetLogger,
)
from .logger_namespace import (
    ApatheticLogging_Internal_Logger,
)


class ApatheticLogging_Internal_LoggingLevels:  # noqa: N801  # pyright: ignore[reportUnusedClass]
    """Mixin class that provides custom log level functions.

    This class contains convenience functions for custom log levels that don't
    exist in the standard library. These functions log to the root logger and
    ensure the logging module is extended with custom levels.

    When mixed into apathetic_logging, it provides functions for TEST, TRACE, DETAIL,
    and BRIEF log levels.
    """

    @staticmethod
    def trace(msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a message with severity 'TRACE' on the root logger.

        TRACE is more verbose than DEBUG. If the logger has no handlers,
        call basicConfig() to add a console handler with a pre-defined format.

        This function gets an apathetic_logging.Logger instance (ensuring
        the root logger is an apathetic logger) and calls its trace() method.
        """
        _get_logger = ApatheticLogging_Internal_GetLogger
        _logger = ApatheticLogging_Internal_Logger
        _constants = ApatheticLogging_Internal_Constants
        # Ensure logging module is extended
        _logger.Logger.extendLoggingModule()
        # Get root logger - it should be an apathetic logger now
        logger = _get_logger.getLogger("", extend=True)
        # Check if logger has trace method (it should if it's an apathetic logger)
        if hasattr(logger, "trace"):
            logger.trace(msg, *args, **kwargs)
        # Fallback: if root logger is still a standard logger, use _log directly
        # This can happen if root logger was created before extendLoggingModule
        elif logger.isEnabledFor(_constants.TRACE_LEVEL):
            logger._log(_constants.TRACE_LEVEL, msg, args, **kwargs)  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

    @staticmethod
    def detail(msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a message with severity 'DETAIL' on the root logger.

        DETAIL is more detailed than INFO. If the logger has no handlers,
        call basicConfig() to add a console handler with a pre-defined format.

        This function gets an apathetic_logging.Logger instance (ensuring
        the root logger is an apathetic logger) and calls its detail() method.
        """
        _get_logger = ApatheticLogging_Internal_GetLogger
        _logger = ApatheticLogging_Internal_Logger
        _constants = ApatheticLogging_Internal_Constants
        # Ensure logging module is extended
        _logger.Logger.extendLoggingModule()
        # Get root logger - it should be an apathetic logger now
        logger = _get_logger.getLogger("", extend=True)
        # Check if logger has detail method (it should if it's an apathetic logger)
        if hasattr(logger, "detail"):
            logger.detail(msg, *args, **kwargs)
        # Fallback: if root logger is still a standard logger, use _log directly
        elif logger.isEnabledFor(_constants.DETAIL_LEVEL):
            logger._log(_constants.DETAIL_LEVEL, msg, args, **kwargs)  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

    @staticmethod
    def brief(msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a message with severity 'BRIEF' on the root logger.

        BRIEF is less detailed than INFO. If the logger has no handlers,
        call basicConfig() to add a console handler with a pre-defined format.

        This function gets an apathetic_logging.Logger instance (ensuring
        the root logger is an apathetic logger) and calls its brief() method.
        """
        _get_logger = ApatheticLogging_Internal_GetLogger
        _logger = ApatheticLogging_Internal_Logger
        _constants = ApatheticLogging_Internal_Constants
        # Ensure logging module is extended
        _logger.Logger.extendLoggingModule()
        # Get root logger - it should be an apathetic logger now
        logger = _get_logger.getLogger("", extend=True)
        # Check if logger has brief method (it should if it's an apathetic logger)
        if hasattr(logger, "brief"):
            logger.brief(msg, *args, **kwargs)
        # Fallback: if root logger is still a standard logger, use _log directly
        elif logger.isEnabledFor(_constants.BRIEF_LEVEL):
            logger._log(_constants.BRIEF_LEVEL, msg, args, **kwargs)  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]

    @staticmethod
    def test(msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a message with severity 'TEST' on the root logger.

        TEST is the most verbose level and bypasses capture. If the logger has no
        handlers, call basicConfig() to add a console handler with a pre-defined format.

        This function gets an apathetic_logging.Logger instance (ensuring
        the root logger is an apathetic logger) and calls its test() method.
        """
        _get_logger = ApatheticLogging_Internal_GetLogger
        _logger = ApatheticLogging_Internal_Logger
        _constants = ApatheticLogging_Internal_Constants
        # Ensure logging module is extended
        _logger.Logger.extendLoggingModule()
        # Get root logger - it should be an apathetic logger now
        logger = _get_logger.getLogger("", extend=True)
        # Check if logger has test method (it should if it's an apathetic logger)
        if hasattr(logger, "test"):
            logger.test(msg, *args, **kwargs)
        # Fallback: if root logger is still a standard logger, use _log directly
        # This can happen if root logger was created before extendLoggingModule
        elif logger.isEnabledFor(_constants.TEST_LEVEL):
            logger._log(_constants.TEST_LEVEL, msg, args, **kwargs)  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
