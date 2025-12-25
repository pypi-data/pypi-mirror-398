# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
import logging
from types import FrameType
from typing import Optional

from core_logging.logger_utils import LoggerType

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#         Defines the public interface of the module that will be imported when using 'from package import *'.         #
#    This helps control what is exposed to the global namespace, limiting imports to only those listed in __all__.     #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = ["InterceptHandler"]


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                Module Implementation                                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


class InterceptHandler(logging.Handler):
    """A logging handler that redirects standard logging messages to a structured logger."""

    def __init__(self, logger: LoggerType, name: Optional[str] = None):
        """Initializes the handler with a structured logger.

        Args:
            logger (LoggerType): The logger instance to intercept log messages.
            name (str, optional): The name of the logging handler. Defaults to None.
        """
        super().__init__()
        self.logger: LoggerType = logger
        if name:
            self.set_name(name)

    def emit(self, record: logging.LogRecord):
        """Processes and forwards log records to the structured logger.

        Args:
            record (logging.LogRecord): The log record to be handled.
        """
        try:
            level = self.logger.level(record.levelname).name
        except ValueError:
            level = record.levelno  # type: ignore

        # Find caller from where originated the logged message
        frame: Optional[FrameType] = logging.currentframe()
        depth: int = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        self.logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())
