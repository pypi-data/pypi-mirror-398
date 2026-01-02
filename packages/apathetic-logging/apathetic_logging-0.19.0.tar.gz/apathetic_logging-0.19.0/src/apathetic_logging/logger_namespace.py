# src/apathetic_logging/logger_namespace.py
"""Logger namespace mixin that provides the Logger nested class.

See https://docs.python.org/3/library/logging.html#logging.Logger for the
complete list of standard library Logger methods.

Docstrings are adapted from the standard library logging.Logger documentation
licensed under the Python Software Foundation License Version 2.
"""

from __future__ import annotations

from .logger import (
    ApatheticLogging_Internal_LoggerCore,
)


class ApatheticLogging_Internal_Logger:  # noqa: N801  # pyright: ignore[reportUnusedClass]
    """Mixin class that provides the Logger nested class.

    This class contains the Logger implementation as a nested class, using
    the core Logger implementation.

    When mixed into apathetic_logging, it provides apathetic_logging.Logger.
    """

    class Logger(
        ApatheticLogging_Internal_LoggerCore,
    ):
        """Logger for all Apathetic tools.

        This Logger class is composed from:
        - Core Logger implementation
          (ApatheticLogging_Internal_LoggerCore, which inherits from logging.Logger)
        """
