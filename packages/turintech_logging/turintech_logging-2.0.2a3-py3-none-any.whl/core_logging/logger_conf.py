# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
import sys
from datetime import time, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

from pydantic import Field, field_validator

from core_common_configuration.base_conf_env import BaseConfEnv

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                           specifies all modules that shall be loaded and imported into the                           #
#                                current namespace when we use 'from package import *'                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = [
    "EnableLoggerConf",
    "LoggerConf",
    "FileLoggerConf",
    "logger_conf_factory",
    "file_logger_conf_factory",
    "enable_logger_conf_factory",
]


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                Logging Configuration                                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


class EnableLoggerConf(BaseConfEnv):
    """Configuration to enable or disable different types of logging."""

    enable: bool = Field(
        True,
        description=(
            "Flag indicating whether the logging configuration should be initialized (True) or if this configuration "
            "is already initialized (False)."
        ),
    )
    enable_file: bool = Field(True, description="Flag to enable (True) or disable (False) logging to a file.")
    enable_stderr: bool = Field(False, description="Flag to enable (True) or disable (False) logging to stderr output.")


class LoggerConf(BaseConfEnv):
    """Configuration attributes for application logs.

    Attributes:
        sink: An object responsible for receiving formatted logging messages and propagating them
            to an appropriate endpoint.
        level: The minimum severity level from which logged messages should be sent to the sink.
        format: The template used to format logged messages before being sent to the sink.
        colorize: Whether the color markups contained in the formatted message should be converted
            to ANSI codes for terminal coloration, or stripped otherwise.
        serialize: Whether the logged message and its records should be first converted to a JSON string
            before being sent to the sink.
        backtrace: Whether the exception trace formatted should be extended upward, beyond the catching point,
            to show the full stack trace which generated the error.
        diagnose: Whether the exception trace should display the variables' values to ease debugging.
            This should be set to False in production to avoid leaking sensitive data.
        enqueue: Whether the messages to be logged should first pass through a multiprocess-safe queue
            before reaching the sink. This is useful while logging to a file through multiple processes
            and also has the advantage of making logging calls non-blocking.
    """

    sink: Union[Path, object]

    level: str = "INFO"
    format: Union[str, Callable] = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>"
        " <r>-</r> <level>{level: <8}</level>"
        " <r>-</r> <cyan>{name}</cyan>.<cyan>{function}</cyan>:<cyan>{line}</cyan>"
        " <r>-</r> <level>{message}</level>"
    )
    colorize: Optional[bool] = True
    serialize: Optional[bool] = False
    backtrace: Optional[bool] = True
    diagnose: Optional[bool] = False
    enqueue: Optional[bool] = True

    @field_validator("level")
    def upper_validator(cls, value: str) -> str:
        return value.upper() if value else value

    @field_validator("sink", mode="before")
    def sink_validator(cls, value: str):
        return {
            "sys.stdout": sys.stdout,
            "sys.stderr": sys.stderr,
        }.get(value, value)

    def model_dump(self, **kwargs) -> dict[str, Any]:
        """Override Pydantic's `model_dump` to exclude the `sink` field when dumping.

        After obtaining the clean dump, re-attach the actual `sink` object (e.g., sys.stdout, file path,
        logging handler) so that `logger.add()` receives a supported sink type.
        """
        dump = super().model_dump(**kwargs, exclude={"sink"})
        return {**dump, "sink": self.sink}


class FileLoggerConf(LoggerConf):
    """Configuration attributes for application file logs."""

    colorize: Optional[bool] = False
    rotation: Union[str, int, time, timedelta] = "12:00"  # New file is created each day at noon
    retention: Union[str, int, time, timedelta] = "1 month"
    compression: Optional[str] = "zip"
    delay: bool = True


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                            Logging Configuration Factory                                             #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def enable_logger_conf_factory(
    _env_file: Optional[str] = None, prefix: Optional[str] = None, defaults: Optional[Dict] = None, **kwargs
) -> EnableLoggerConf:
    """This is a factory generating a EnableLoggerConf class specific to a service, loading every value from a generic
    .env file storing variables in uppercase with a service prefix.

    example .env:
       PREFIX_ENABLE=true
       ...

    Args:
        _env_file (str, optional): Configuration file of the environment variables from where to load the values.
        prefix (str, optional): Prefix that the class attributes must have in the environment variables.
        defaults (Dict, optional): New values to override the default field values for the configuration model.
        kwargs (**Dict): Arguments passed to the Settings class initializer.

    Returns:
        conf (EnableLoggerConf): Object of the required configuration class

    """
    return EnableLoggerConf.with_defaults(env_file=_env_file, env_prefix=prefix, defaults=defaults, **kwargs)


def logger_conf_factory(
    _env_file: Optional[str] = None, prefix: Optional[str] = None, defaults: Optional[Dict] = None, **kwargs
) -> LoggerConf:
    """This is a factory generating a LoggerConf class specific to a service, loading every value from a generic .env
    file storing variables in uppercase with a service prefix.

    example .env:
       PREFIX_LEVEL=INFO
       ...

    Args:
        _env_file (str, optional): Configuration file of the environment variables from where to load the values.
        prefix (str, optional): Prefix that the class attributes must have in the environment variables.
        defaults (Dict, optional): New values to override the default field values for the configuration model.
        kwargs (**Dict): Arguments passed to the Settings class initializer.

    Returns:
        conf (LoggerConf): Object of the required configuration class

    """
    return LoggerConf.with_defaults(env_file=_env_file, env_prefix=prefix, defaults=defaults, **kwargs)


def file_logger_conf_factory(
    _env_file: Optional[str] = None, prefix: Optional[str] = None, defaults: Optional[Dict] = None, **kwargs
) -> FileLoggerConf:
    """This is a factory generating a FileLoggerConf class specific to a service, loading every value from a generic
    .env file storing variables in uppercase with a service prefix.

    example .env:
       PREFIX_LEVEL=INFO
       PREFIX_COLORIZE=true
       ...

    Args:
        _env_file (str, optional): Configuration file of the environment variables from where to load the values.
        prefix (str, optional): Prefix that the class attributes must have in the environment variables.
        defaults (Dict, optional): New values to override the default field values for the configuration model.
        kwargs (**Dict): Arguments passed to the Settings class initializer.

    Returns:
        conf (FileLoggerConf): Object of the required configuration class

    """
    return FileLoggerConf.with_defaults(env_file=_env_file, env_prefix=prefix, defaults=defaults, **kwargs)
