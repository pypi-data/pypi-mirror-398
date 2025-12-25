# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
from core_logging.logger_conf import EnableLoggerConf, FileLoggerConf, LoggerConf
from core_logging.logger_handler import InterceptHandler
from core_logging.logger_service import LoggerService
from core_logging.logger_utils import LoggerType, get_logger

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#         Defines the public interface of the module that will be imported when using 'from package import *'.         #
#    This helps control what is exposed to the global namespace, limiting imports to only those listed in __all__.     #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = [
    "EnableLoggerConf",
    "FileLoggerConf",
    "LoggerConf",
    "InterceptHandler",
    "LoggerService",
    "get_logger",
    "LoggerType",
    "logger",
]

logger = get_logger()
