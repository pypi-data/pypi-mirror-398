# src/apathetic_logging/namespace.py
"""Shared Apathetic CLI logger implementation.

See https://docs.python.org/3/library/logging.html for the complete list of
standard library logging functions that are wrapped by this namespace.

Docstrings are adapted from the standard library logging module documentation
licensed under the Python Software Foundation License Version 2.
"""

from __future__ import annotations

from .constants import (
    ApatheticLogging_Internal_Constants,
)
from .dual_stream_handler import (
    ApatheticLogging_Internal_DualStreamHandler,
)
from .get_logger import (
    ApatheticLogging_Internal_GetLogger,
)
from .logger_namespace import (
    ApatheticLogging_Internal_Logger,
)
from .logging_levels import (
    ApatheticLogging_Internal_LoggingLevels,
)
from .logging_root import (
    ApatheticLogging_Internal_LoggingRoot,
)
from .logging_std_camel import (
    ApatheticLogging_Internal_StdCamelCase,
)
from .logging_utils import (
    ApatheticLogging_Internal_LoggingUtils,
)
from .registry import (
    ApatheticLogging_Internal_Registry,
)
from .registry_data import (
    ApatheticLogging_Internal_RegistryData,
)
from .safe_logging import (
    ApatheticLogging_Internal_SafeLogging,
)
from .tag_formatter import (
    ApatheticLogging_Internal_TagFormatter,
)


# --- Apathetic Logging Namespace -------------------------------------------


class apathetic_logging(  # noqa: N801
    ApatheticLogging_Internal_Constants,
    ApatheticLogging_Internal_DualStreamHandler,
    ApatheticLogging_Internal_GetLogger,
    ApatheticLogging_Internal_Logger,
    ApatheticLogging_Internal_LoggingLevels,
    ApatheticLogging_Internal_LoggingRoot,
    ApatheticLogging_Internal_LoggingUtils,
    ApatheticLogging_Internal_Registry,
    ApatheticLogging_Internal_RegistryData,
    ApatheticLogging_Internal_SafeLogging,
    ApatheticLogging_Internal_TagFormatter,
    ApatheticLogging_Internal_StdCamelCase,  # keep last
):
    """Namespace for apathetic logging functionality.

    All logger functionality is accessed via this namespace class to minimize
    global namespace pollution when the library is embedded in a stitched script.

    **Classes:**
    - ``Logger`` → ``ApatheticLogging_Internal_Logger``
    - ``TagFormatter`` → ``ApatheticLogging_Internal_TagFormatter``
    - ``DualStreamHandler`` → ``ApatheticLogging_Internal_DualStreamHandler``

    **Static Methods:**
    - ``getLogger()`` → ``ApatheticLogging_Internal_GetLogger``
    - ``registerDefaultLogLevel()`` → ``ApatheticLogging_Internal_Registry``
    - ``registerLogLevelEnvVars()`` → ``ApatheticLogging_Internal_Registry``
    - ``registerLogger()`` → ``ApatheticLogging_Internal_Registry``
    - ``safeLog()`` → ``ApatheticLogging_Internal_SafeLogging``
    - ``safeTrace()`` → ``ApatheticLogging_Internal_SafeLogging``
    - ``makeSafeTrace()`` → ``ApatheticLogging_Internal_SafeLogging``

    **Constants:**
    - ``DEFAULT_APATHETIC_LOG_LEVEL`` → ``ApatheticLogging_Internal_Constants``
    - ``DEFAULT_APATHETIC_LOG_LEVEL_ENV_VARS`` → ``ApatheticLogging_Internal_Constants``
    - ``SAFE_TRACE_ENABLED`` → ``ApatheticLogging_Internal_SafeLogging``
    - ``TEST_LEVEL`` → ``ApatheticLogging_Internal_Constants``
    - ``TRACE_LEVEL`` → ``ApatheticLogging_Internal_Constants``
    - ``BRIEF_LEVEL`` → ``ApatheticLogging_Internal_Constants``
    - ``DETAIL_LEVEL`` → ``ApatheticLogging_Internal_Constants``
    - ``SILENT_LEVEL`` → ``ApatheticLogging_Internal_Constants``
    - ``LEVEL_ORDER`` → ``ApatheticLogging_Internal_Constants``
    - ``ANSIColors`` → ``ApatheticLogging_Internal_Constants``
    - ``TAG_STYLES`` → ``ApatheticLogging_Internal_Constants``
    """


# Ensure logging module is extended with TEST, TRACE, DETAIL, BRIEF, and SILENT
# levels
# This must be called before any loggers are created
# This runs when namespace.py is executed (both package and stitched modes)
# The method is idempotent, so safe to call multiple times if needed
apathetic_logging.Logger.extendLoggingModule()

# Note: All exports are handled in __init__.py
# - For library builds (package/stitched): __init__.py is included, exports happen
# - For embedded builds: __init__.py is excluded, no exports (only class available)
