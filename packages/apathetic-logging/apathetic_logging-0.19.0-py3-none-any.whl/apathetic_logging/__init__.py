# src/apathetic_logging/__init__.py
"""Apathetic Logging implementation."""

from typing import TYPE_CHECKING, TypeAlias, cast


if TYPE_CHECKING:
    from .logger_namespace import ApatheticLogging_Internal_Logger
    from .namespace import apathetic_logging as _apathetic_logging_class

# Get reference to the namespace class
# In stitched mode: class is already defined in namespace.py (executed before this)
# In package mode: import from namespace module
_apathetic_logging_is_stitched = globals().get("__STITCHED__", False)

if _apathetic_logging_is_stitched:
    # Stitched mode: class already defined in namespace.py
    # Get reference to the class (it's already in globals from namespace.py)
    _apathetic_logging_raw = globals().get("apathetic_logging")
    if _apathetic_logging_raw is None:
        # Fallback: should not happen, but handle gracefully
        msg = "apathetic_logging class not found in stitched mode"
        raise RuntimeError(msg)
    # Type cast to help mypy understand this is the apathetic_logging class
    # The import gives us type[apathetic_logging], so cast to
    # type[_apathetic_logging_class]
    apathetic_logging = cast("type[_apathetic_logging_class]", _apathetic_logging_raw)
else:
    # Package mode: import from namespace module
    # This block is only executed in package mode, not in stitched builds
    from .namespace import apathetic_logging

    # Ensure the else block is not empty (build script may remove import)
    _ = apathetic_logging

# Export all namespace items for convenience
# These are aliases to apathetic_logging.*
#
# Note: In embedded builds, __init__.py is excluded from the stitch,
# so this code never runs and no exports happen (only the class is available).
# In stitched/package builds, __init__.py is included, so exports happen.
DEFAULT_APATHETIC_LOG_LEVEL = apathetic_logging.DEFAULT_APATHETIC_LOG_LEVEL
DEFAULT_APATHETIC_LOG_LEVEL_ENV_VARS = (
    apathetic_logging.DEFAULT_APATHETIC_LOG_LEVEL_ENV_VARS
)
LEVEL_ORDER = apathetic_logging.LEVEL_ORDER
SILENT_LEVEL = apathetic_logging.SILENT_LEVEL
TAG_STYLES = apathetic_logging.TAG_STYLES
TEST_LEVEL = apathetic_logging.TEST_LEVEL
safeTrace = apathetic_logging.safeTrace
SAFE_TRACE_ENABLED = apathetic_logging.SAFE_TRACE_ENABLED
TRACE_LEVEL = apathetic_logging.TRACE_LEVEL
BRIEF_LEVEL = apathetic_logging.BRIEF_LEVEL
DETAIL_LEVEL = apathetic_logging.DETAIL_LEVEL
INHERIT_LEVEL = apathetic_logging.INHERIT_LEVEL
NOTSET_LEVEL = apathetic_logging.NOTSET_LEVEL
ROOT_ALLOW_ALL_LEVEL = apathetic_logging.ROOT_ALLOW_ALL_LEVEL

# ANSI Colors
ANSIColors = apathetic_logging.ANSIColors

# Classes
DualStreamHandler = apathetic_logging.DualStreamHandler
TagFormatter = apathetic_logging.TagFormatter
# Logger is a nested class in ApatheticLogging_Internal_Logger that
# inherits from logging.Logger.
# Use TypeAlias to help mypy understand this is a class type.
if TYPE_CHECKING:
    Logger: TypeAlias = ApatheticLogging_Internal_Logger.Logger
else:
    Logger = apathetic_logging.Logger

# Functions (camelCase - stdlib wrappers)
addLevelName = apathetic_logging.addLevelName
basicConfig = apathetic_logging.basicConfig
captureWarnings = apathetic_logging.captureWarnings
critical = apathetic_logging.critical
currentframe = apathetic_logging.currentframe
debug = apathetic_logging.debug
detail = apathetic_logging.detail
disable = apathetic_logging.disable
error = apathetic_logging.error
exception = apathetic_logging.exception
fatal = apathetic_logging.fatal
getHandlerByName = apathetic_logging.getHandlerByName
getHandlerNames = apathetic_logging.getHandlerNames
getLevelName = apathetic_logging.getLevelName
getLevelNamesMapping = apathetic_logging.getLevelNamesMapping
getLogRecordFactory = apathetic_logging.getLogRecordFactory
getLogger = apathetic_logging.getLogger
getLoggerClass = apathetic_logging.getLoggerClass
info = apathetic_logging.info
log = apathetic_logging.log
makeLogRecord = apathetic_logging.makeLogRecord
brief = apathetic_logging.brief
setLogRecordFactory = apathetic_logging.setLogRecordFactory
setLoggerClass = apathetic_logging.setLoggerClass
setRootLevel = apathetic_logging.setRootLevel
shutdown = apathetic_logging.shutdown
test = apathetic_logging.test
trace = apathetic_logging.trace
warn = apathetic_logging.warn
warning = apathetic_logging.warning

# Functions (camelCase - library functions)
getCompatibilityMode = apathetic_logging.getCompatibilityMode
getDefaultLogLevel = apathetic_logging.getDefaultLogLevel
getDefaultLoggerName = apathetic_logging.getDefaultLoggerName
getDefaultPropagate = apathetic_logging.getDefaultPropagate
getEffectiveRootLevel = apathetic_logging.getEffectiveRootLevel
getEffectiveRootLevelName = apathetic_logging.getEffectiveRootLevelName
getLevelName = apathetic_logging.getLevelName
getLevelNameStr = apathetic_logging.getLevelNameStr
getLevelNumber = apathetic_logging.getLevelNumber
getLogLevelEnvVars = apathetic_logging.getLogLevelEnvVars
getLoggerOfType = apathetic_logging.getLoggerOfType
getRegisteredLoggerName = apathetic_logging.getRegisteredLoggerName
getRootLevel = apathetic_logging.getRootLevel
getRootLevelName = apathetic_logging.getRootLevelName
getRootLogger = apathetic_logging.getRootLogger  # pyright: ignore[reportUnknownVariableType,reportUnknownMemberType]
getTargetPythonVersion = apathetic_logging.getTargetPythonVersion
hasLogger = apathetic_logging.hasLogger
makeSafeTrace = apathetic_logging.makeSafeTrace
registerDefaultLogLevel = apathetic_logging.registerDefaultLogLevel
registerLogLevelEnvVars = apathetic_logging.registerLogLevelEnvVars
registerLogger = apathetic_logging.registerLogger
registerCompatibilityMode = apathetic_logging.registerCompatibilityMode
registerPortHandlers = apathetic_logging.registerPortHandlers
registerPortLevel = apathetic_logging.registerPortLevel
registerPropagate = apathetic_logging.registerPropagate
registerReplaceRootLogger = apathetic_logging.registerReplaceRootLogger
registerTargetPythonVersion = apathetic_logging.registerTargetPythonVersion
removeLogger = apathetic_logging.removeLogger
safeLog = apathetic_logging.safeLog
setRootLevel = apathetic_logging.setRootLevel
setRootLevelMinimum = apathetic_logging.setRootLevelMinimum
useRootLevel = apathetic_logging.useRootLevel
useRootLevelMinimum = apathetic_logging.useRootLevelMinimum
isRootEnabledFor = apathetic_logging.isRootEnabledFor
logRootDynamic = apathetic_logging.logRootDynamic


__all__ = [
    "BRIEF_LEVEL",
    "DEFAULT_APATHETIC_LOG_LEVEL",
    "DEFAULT_APATHETIC_LOG_LEVEL_ENV_VARS",
    "DETAIL_LEVEL",
    "INHERIT_LEVEL",
    "LEVEL_ORDER",
    "NOTSET_LEVEL",
    "ROOT_ALLOW_ALL_LEVEL",
    "SAFE_TRACE_ENABLED",
    "SILENT_LEVEL",
    "TAG_STYLES",
    "TEST_LEVEL",
    "TRACE_LEVEL",
    "ANSIColors",
    "DualStreamHandler",
    "Logger",
    "TagFormatter",
    "addLevelName",
    "apathetic_logging",
    "basicConfig",
    "brief",
    "captureWarnings",
    "critical",
    "currentframe",
    "debug",
    "detail",
    "disable",
    "error",
    "exception",
    "fatal",
    "getCompatibilityMode",
    "getDefaultLogLevel",
    "getDefaultLoggerName",
    "getDefaultPropagate",
    "getEffectiveRootLevel",
    "getEffectiveRootLevelName",
    "getHandlerByName",
    "getHandlerNames",
    "getLevelName",
    "getLevelNameStr",
    "getLevelNamesMapping",
    "getLevelNumber",
    "getLogLevelEnvVars",
    "getLogRecordFactory",
    "getLogger",
    "getLoggerClass",
    "getLoggerOfType",
    "getRegisteredLoggerName",
    "getRootLevel",
    "getRootLevelName",
    "getRootLogger",
    "getTargetPythonVersion",
    "hasLogger",
    "info",
    "isRootEnabledFor",
    "log",
    "logRootDynamic",
    "makeLogRecord",
    "makeSafeTrace",
    "registerCompatibilityMode",
    "registerDefaultLogLevel",
    "registerLogLevelEnvVars",
    "registerLogger",
    "registerPortHandlers",
    "registerPortLevel",
    "registerPropagate",
    "registerReplaceRootLogger",
    "registerTargetPythonVersion",
    "removeLogger",
    "safeLog",
    "safeTrace",
    "setLogRecordFactory",
    "setLoggerClass",
    "setRootLevel",
    "setRootLevelMinimum",
    "shutdown",
    "test",
    "trace",
    "useRootLevel",
    "useRootLevelMinimum",
    "warn",
    "warning",
]
