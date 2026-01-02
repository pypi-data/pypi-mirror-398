# src/apathetic_logging/dual_stream_handler.py
"""DualStreamHandler class for Apathetic Logging.

Docstrings are adapted from the standard library logging.Handler documentation
licensed under the Python Software Foundation License Version 2.
"""

from __future__ import annotations

import logging
import sys
from typing import Any


class ApatheticLogging_Internal_DualStreamHandler:  # noqa: N801  # pyright: ignore[reportUnusedClass]
    """Mixin class that provides the DualStreamHandler nested class.

    This class contains the DualStreamHandler implementation as a nested class.
    When mixed into apathetic_logging, it provides apathetic_logging.DualStreamHandler.
    """

    class DualStreamHandler(logging.StreamHandler):  # type: ignore[type-arg]
        """Send info to stdout, everything else to stderr.

        INFO, BRIEF, and DETAIL go to stdout (normal program output).
        TRACE, DEBUG, WARNING, ERROR, and CRITICAL go to stderr
        (diagnostic/error output).
        When logger level is TEST, TEST/TRACE/DEBUG messages bypass capture
        by writing to sys.__stderr__ instead of sys.stderr. This allows
        debugging tests without breaking output assertions while still being
        capturable by subprocess.run(capture_output=True).
        WARNING, ERROR, and CRITICAL always use normal stderr, even in TEST mode.
        """

        enable_color: bool = False
        """Enable ANSI color output for log messages."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            """Initialize the dual stream handler. super().__init__() to StreamHandler.

            Args:
                *args: Additional positional arguments (for future-proofing)
                **kwargs: Additional keyword arguments (for future-proofing)
            """
            # default to stdout, overridden per record in emit()
            super().__init__(*args, **kwargs)  # pyright: ignore[reportUnknownMemberType]

        def emit(self, record: logging.LogRecord, *args: Any, **kwargs: Any) -> None:
            """Routes based on log level and handles colorization.

            Features:
            - Routes messages to stdout or stderr based on log level:
              - DETAIL, INFO, and BRIEF → stdout (normal program output)
              - TRACE, DEBUG, WARNING, ERROR, and CRITICAL → stderr
                (diagnostic/error output)
            - In TEST mode, TEST/TRACE/DEBUG messages bypass pytest capture
              by writing to sys.__stderr__ instead of sys.stderr
            - Sets enable_color attribute on record for TagFormatter integration

            Args:
                record: The LogRecord to emit
                *args: Additional positional arguments (for future-proofing)
                **kwargs: Additional keyword arguments (for future-proofing)

            logging.Handler.emit() implementation:
            https://docs.python.org/3.10/library/logging.html#logging.Handler.emit
            """
            # Import here to avoid circular dependency
            from .constants import (  # noqa: PLC0415
                ApatheticLogging_Internal_Constants,
            )

            _constants = ApatheticLogging_Internal_Constants
            level = record.levelno

            # Check if logger is in TEST mode (bypass capture for verbose levels)
            logger_name = record.name
            # from .get_logger import (
            #     ApatheticLogging_Internal_GetLogger,
            # )

            # logger_instance = ApatheticLogging_Internal_GetLogger.getLogger(
            #     logger_name, extend=False
            # )
            # can't use internal getLogger() here
            #   because then it will call extendLoggingModule again
            logger_instance = logging.getLogger(logger_name)

            # Use duck typing to check if this is our Logger class
            # (has test() method) to avoid circular dependency
            has_test_method = hasattr(logger_instance, "test") and callable(
                getattr(logger_instance, "test", None)
            )
            # Use effective level (not explicit level) to detect TEST mode,
            # so child loggers that inherit TEST level from parent are correctly
            # detected
            is_test_mode = has_test_method and logger_instance.getEffectiveLevel() == (
                _constants.TEST_LEVEL
            )

            # Determine target stream
            if level >= logging.WARNING:
                # WARNING, ERROR, CRITICAL → stderr (always, even in TEST mode)
                # This ensures they still break tests as expected
                self.stream = sys.stderr
            elif level <= logging.DEBUG:
                # TEST, TRACE, DEBUG → stderr (normal) or __stderr__ (TEST mode bypass)
                # Use __stderr__ so they bypass pytest capsys but are still
                # capturable by subprocess.run(capture_output=True)
                if is_test_mode:
                    self.stream = sys.__stderr__
                else:
                    self.stream = sys.stderr
            else:
                # DETAIL, INFO, BRIEF → stdout (normal program output)
                self.stream = sys.stdout

            # used by TagFormatter
            record.enable_color = getattr(self, "enable_color", False)

            super().emit(record, *args, **kwargs)
