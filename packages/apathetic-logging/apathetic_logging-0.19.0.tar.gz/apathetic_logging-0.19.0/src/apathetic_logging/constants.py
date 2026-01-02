# src/apathetic_logging/constants.py
"""Constants for Apathetic Logging."""

from __future__ import annotations

import logging
from typing import ClassVar


class ApatheticLogging_Internal_Constants:  # noqa: N801  # pyright: ignore[reportUnusedClass]
    """Constants for apathetic logging functionality.

    This class contains all constant values used by apathetic_logging.
    It's kept separate for organizational purposes.
    """

    DEFAULT_APATHETIC_LOG_LEVEL: str = "detail"
    """Default log level when no other source is found."""

    DEFAULT_APATHETIC_LOG_LEVEL_ENV_VARS: ClassVar[list[str]] = ["LOG_LEVEL"]
    """Default environment variable names to check for log level."""

    INHERIT_LEVEL: int = logging.NOTSET
    """INHERIT level (0) - logger inherits level from parent.

    This is the preferred constant name. Use INHERIT_LEVEL in new code.
    Equivalent to stdlib logging.NOTSET.
    """

    NOTSET_LEVEL: int = INHERIT_LEVEL
    """NOTSET level (0) - logger inherits level from parent.

    Alias for INHERIT_LEVEL, kept for compatibility with stdlib
    logging.NOTSET terminology. Use INHERIT_LEVEL in new code for clarity.
    """

    ROOT_ALLOW_ALL_LEVEL: int = logging.NOTSET
    """Root logger accepts all messages level (0).

    When the root logger is set to this level, it accepts all messages
    without filtering, regardless of severity. This is stdlib logging behavior:
    a logger set to NOTSET (0) processes all messages (unlike child loggers
    which inherit from parent when NOTSET).

    Note: Use ROOT_ALLOW_ALL_LEVEL when explicitly setting root to accept
    all messages for clarity. Equivalent to logging.NOTSET.
    """

    # levels must be careful not to equal 0 to avoid INHERIT_LEVEL (i.e. NOTSET)
    TEST_LEVEL: int = logging.DEBUG - 8
    """Most verbose level, bypasses capture."""

    TRACE_LEVEL: int = logging.DEBUG - 5
    """More verbose than DEBUG."""

    DETAIL_LEVEL: int = logging.INFO - 5
    """More detailed than INFO."""

    BRIEF_LEVEL: int = logging.INFO + 5
    """Less detailed than INFO."""

    SILENT_LEVEL: int = logging.CRITICAL + 1
    """Disables all logging (one above the highest builtin level)."""

    LEVEL_ORDER: ClassVar[list[str]] = [
        "test",  # most verbose, bypasses capture for debugging tests
        "trace",
        "debug",
        "detail",
        "info",
        "brief",
        "warning",
        "error",
        "critical",
        "silent",  # disables all logging
    ]
    """Ordered list of log level names from most to least verbose."""

    class ANSIColors:
        """A selection of ANSI color code constants.

        For a comprehensive reference on ANSI escape codes and color support,
        see: https://en.wikipedia.org/wiki/ANSI_escape_code#Colors
        """

        RESET: str = "\033[0m"
        """Reset ANSI color codes."""

        CYAN: str = "\033[36m"
        """Cyan ANSI color code."""

        YELLOW: str = "\033[93m"  # or \033[33m
        """Yellow ANSI color code."""

        RED: str = "\033[91m"  # or \033[31m # or background \033[41m
        """Red ANSI color code."""

        GREEN: str = "\033[92m"  # or \033[32m
        """Green ANSI color code."""

        GRAY: str = "\033[90m"
        """Gray ANSI color code."""

    TAG_STYLES: ClassVar[dict[str, tuple[str, str]]] = {
        "TEST": (ANSIColors.GRAY, "[TEST]"),
        "TRACE": (ANSIColors.GRAY, "[TRACE]"),
        "DEBUG": (ANSIColors.CYAN, "[DEBUG]"),
        "WARNING": ("", "⚠️ "),
        "ERROR": ("", "❌ "),
        "CRITICAL": ("", "💥 "),
    }
    """Mapping of level names to (color_code, tag_text) tuples."""

    TARGET_PYTHON_VERSION: tuple[int, int] | None = None
    """Target Python version (major, minor).

    If None, target version checks are disabled by default.
    """

    DEFAULT_PROPAGATE: bool = True
    """Default propagate setting for loggers.

    When True, loggers propagate messages to parent loggers, allowing
    centralized control via root logger. Only root logger has handlers
    to avoid duplicate messages.
    """

    DEFAULT_MANAGE_HANDLERS: bool = True
    """Default value for manage_handlers parameter in setPropagate().

    When True (default), setPropagate() automatically manages apathetic
    handlers based on propagate setting. When False, only sets propagate
    without managing handlers. In compat_mode, this may default to False.
    """

    ROOT_LOGGER_KEY: str = ""
    """Key used to retrieve the root logger via logging.getLogger("").

    The root logger is retrieved using an empty string as the logger name.
    """

    ROOT_LOGGER_NAME: str = "root"
    """Name attribute of the root logger instance.

    Note: logging.getLogger("") returns the root logger, but its .name
    attribute is "root" (not ""). This constant represents the actual
    name attribute value of the root logger instance.
    """

    DEFAULT_REPLACE_ROOT_LOGGER: bool = True
    """Default value for whether to replace root logger if it's not the correct type.

    When True (default), extendLoggingModule() will replace the root logger
    if it's not an instance of the apathetic logger class, ensuring the root
    logger has apathetic logger methods like manageHandlers(), trace(), etc.
    When False, the root logger will not be replaced, allowing applications
    to use their own custom logger class for the root logger.
    """

    DEFAULT_PORT_HANDLERS: bool = True
    """Default value for whether to port handlers when replacing a logger.

    When True (default), handlers from the old logger are ported to the new logger,
    preserving existing configuration. When False, the new apathetic logger manages
    its own handlers via manageHandlers() (may conflict with ported handlers).
    """

    DEFAULT_PORT_LEVEL: bool = True
    """Default value for whether to port level when replacing a logger.

    When True (default), the log level is ported from the old logger to the new
    logger, preserving existing configuration. When False, the new logger uses
    apathetic defaults (determineLogLevel() for root logger, INHERIT_LEVEL for
    leaf loggers). Note: User-provided level parameters in getLogger/getLoggerOfType
    take precedence over ported level.
    """
