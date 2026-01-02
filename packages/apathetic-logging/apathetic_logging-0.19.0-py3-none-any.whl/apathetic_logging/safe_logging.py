# src/apathetic_logging/safe_logging.py
"""Safe logging utilities for Apathetic Logging."""

from __future__ import annotations

import builtins
import importlib
import logging
import os
import sys
from collections.abc import Callable
from contextlib import suppress
from typing import Any, ClassVar, TextIO, cast

from .constants import (
    ApatheticLogging_Internal_Constants,
)


# Lazy, safe import — avoids patched time modules
#   in environments like pytest or eventlet
_apatheticlogging_internal_real_time = importlib.import_module("time")


class ApatheticLogging_Internal_SafeLogging:  # noqa: N801  # pyright: ignore[reportUnusedClass]
    """Mixin class that provides safe logging utilities.

    This class contains both safeLog and safeTrace implementations as static
    methods. When mixed into apathetic_logging, it provides:
    - apathetic_logging.safeLog
    - apathetic_logging.safeTrace
    - apathetic_logging.makeSafeTrace
    """

    @staticmethod
    def isSafeTraceEnabled() -> bool:  # noqa: PLR0911
        """Check if safe trace should be enabled.

        Safe trace is enabled when:
        1. SAFE_TRACE env var is set to "1", "true", or "yes"
        2. LOG_LEVEL env var (case insensitive) is "TRACE" or "TEST"
        3. LOG_LEVEL numeric value <= TRACE_LEVEL numeric value

        Returns:
            True if safe trace should be enabled, False otherwise.
        """
        # Check SAFE_TRACE env var
        safe_trace_env = os.getenv("SAFE_TRACE", "").lower()
        if safe_trace_env in {"1", "true", "yes"}:
            return True

        # Check LOG_LEVEL env var
        log_level_env = os.getenv("LOG_LEVEL", "")
        if not log_level_env:
            return False

        log_level_upper = log_level_env.upper()

        # Check if LOG_LEVEL is "TRACE" or "TEST" (case insensitive)
        if log_level_upper in {"TRACE", "TEST"}:
            return True

        # Check if LOG_LEVEL numeric value <= TRACE_LEVEL
        # First try to parse as integer directly
        try:
            log_level_numeric = int(log_level_env)
            if log_level_numeric <= ApatheticLogging_Internal_Constants.TRACE_LEVEL:
                return True
        except ValueError:
            # Not a numeric string, try to look up in logging module
            # This handles cases like "DEBUG", "INFO", etc.
            try:
                level_attr = getattr(logging, log_level_upper, None)
                if (
                    isinstance(level_attr, int)
                    and level_attr <= ApatheticLogging_Internal_Constants.TRACE_LEVEL
                ):
                    return True
            except Exception:  # noqa: BLE001, S110
                # If anything goes wrong, just ignore this check
                pass

        return False

    SAFE_TRACE_ENABLED: ClassVar[bool] = isSafeTraceEnabled()
    """Enable safe trace diagnostics.

    Controlled by:
    - SAFE_TRACE env var (set to "1", "true", or "yes")
    - LOG_LEVEL env var (case insensitive) set to "TRACE" or "TEST"
    - LOG_LEVEL numeric value <= TRACE_LEVEL numeric value

    This can be overridden by tests by assigning directly to this class attribute.
    """

    @staticmethod
    def safeLog(msg: str) -> None:
        """Emergency logger that never fails."""
        stream = cast("TextIO", sys.__stderr__)
        try:
            print(msg, file=stream)
        except Exception:  # noqa: BLE001
            # As final guardrail — never crash during crash reporting
            with suppress(Exception):
                stream.write(f"[INTERNAL] {msg}\n")

    @staticmethod
    def makeSafeTrace(icon: str = "🧪") -> Callable[..., Any]:
        """Create a trace function with a custom icon. Assign it to a variable.

        Args:
            icon: Emoji prefix/suffix for easier visual scanning

        Returns:
            A callable trace function
        """
        _safe_logging = ApatheticLogging_Internal_SafeLogging

        def localTrace(label: str, *args: Any) -> Any:
            return _safe_logging.safeTrace(label, *args, icon=icon)

        return localTrace

    @staticmethod
    def safeTrace(label: str, *args: Any, icon: str = "🧪") -> None:
        """Emit a synchronized, flush-safe diagnostic line.

        Mainly for troubleshooting and tests, avoids the
        logging framework and capture systems, can work even
        pre-logging framework initialization.

        Args:
            label: Short identifier or context string.
            *args: Optional values to append.
            icon: Emoji prefix/suffix for easier visual scanning.

        """
        # Check class attribute to allow tests to override it
        if not ApatheticLogging_Internal_SafeLogging.SAFE_TRACE_ENABLED:
            return

        ts = _apatheticlogging_internal_real_time.monotonic()
        # builtins.print more reliable than sys.stdout.write + sys.stdout.flush
        builtins.print(
            f"{icon} [SAFE TRACE {ts:.6f}] {label}",
            *args,
            file=sys.__stderr__,
            flush=True,
        )
