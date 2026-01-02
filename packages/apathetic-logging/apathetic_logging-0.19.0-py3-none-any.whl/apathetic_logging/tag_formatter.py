# src/apathetic_logging/tag_formatter.py
"""TagFormatter class for Apathetic Logging.

Docstrings are adapted from the standard library logging.Formatter documentation
licensed under the Python Software Foundation License Version 2.
"""

from __future__ import annotations

import logging
from typing import Any

from .constants import (
    ApatheticLogging_Internal_Constants,
)


class ApatheticLogging_Internal_TagFormatter:  # noqa: N801  # pyright: ignore[reportUnusedClass]
    """Mixin class that provides the TagFormatter nested class.

    This class contains the TagFormatter implementation as a nested class.
    When mixed into apathetic_logging, it provides apathetic_logging.TagFormatter.
    """

    class TagFormatter(logging.Formatter):
        """Formatter that adds level tags to log messages.

        Adds colored or plain text tags (e.g., [DEBUG], [ERROR]) based on
        log level. Color support is controlled by the enable_color attribute
        on the LogRecord.
        """

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            """Initialize the TagFormatter.

            Wrapper for logging.Formatter.__init__ with future-proofing.
            """
            super().__init__(*args, **kwargs)

        def format(
            self,
            record: logging.LogRecord,
            *args: Any,
            **kwargs: Any,
        ) -> str:
            """Format a log record with level tag prefix.

            Args:
                record: LogRecord to format
                *args: Additional positional arguments (for future-proofing)
                **kwargs: Additional keyword arguments (for future-proofing)

            Returns:
                Formatted message with optional level tag prefix
            """
            _constants = ApatheticLogging_Internal_Constants
            tag_color, tag_text = _constants.TAG_STYLES.get(record.levelname, ("", ""))
            msg = super().format(record, *args, **kwargs)
            if tag_text:
                if getattr(record, "enable_color", False) and tag_color:
                    prefix = f"{tag_color}{tag_text}{_constants.ANSIColors.RESET}"
                else:
                    prefix = tag_text
                return f"{prefix} {msg}"
            return msg
