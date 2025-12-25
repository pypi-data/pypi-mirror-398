# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
import logging
import sys
from os import PathLike
from typing import Any, Optional

from core_common_configuration import BaseConfManager
from core_logging.logger_conf import EnableLoggerConf, FileLoggerConf, LoggerConf
from core_logging.logger_handler import InterceptHandler
from core_logging.logger_utils import LoggerType, get_logger

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#         Defines the public interface of the module that will be imported when using 'from package import *'.         #
#    This helps control what is exposed to the global namespace, limiting imports to only those listed in __all__.     #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = ["LoggerService"]


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                Service implementation                                                #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


class LoggerService:
    """Manages logging configurations and initialisation.

    This class handles the configuration of logging settings, including enabling or disabling

    Attributes:
        _env_prefix (str): Prefix for environment variable names.
        _conf_mgr (BaseConfManager): Configuration manager for handling environment variables.
        _defaults_enable_logger_conf (Optional[dict[str, Any]]): Default configurations for enabling logging.
        _defaults_logger_conf (Optional[dict[str, Any]]): Default configurations for logger settings.
        _defaults_file_logger_conf (Optional[dict[str, Any]]): Default configurations for file logger settings.
        _extra (Optional[dict[str, str]]): Additional parameters for the core logger.
        _mandatory_logger_conf (dict[str, dict[str, Any]]): Mandatory logger configurations.
    """

    _env_prefix: str
    _conf_mgr: BaseConfManager
    _defaults_enable_logger_conf: Optional[dict[str, Any]]
    _defaults_logger_conf: Optional[dict[str, Any]]
    _defaults_file_logger_conf: Optional[dict[str, Any]]
    _extra: Optional[dict[str, str]]
    _mandatory_logger_conf: dict[str, dict[str, Any]]

    def __init__(
        self,
        env_prefix: str = "LOGGER_",
        env_file: Optional[PathLike] = None,
        mandatory_logger_conf: Optional[dict[str, dict[str, Any]]] = None,
        extra: Optional[dict[str, str]] = None,
        **kwargs,
    ):
        """Initialises the LoggerService with specified configurations.

        Args:
            env_prefix (str): Prefix for environment variable names.
            env_file (str | Path, optional): Path to the environment variable configuration file.
            mandatory_logger_conf (dict[str, dict[str, Any]], optional): Mandatory logger configurations.
            extra (dict[str, str], optional): Additional parameters for the core logger.
            **kwargs: Additional keyword arguments, including:
                - defaults_enable_logger_conf (dict[str, Any], optional): Default configurations for enabling logging.
                - defaults_logger_conf (dict[str, Any], optional): Default configurations for logger settings.
                - defaults_file_logger_conf (dict[str, Any], optional): Default configurations for file logger settings.
        """
        self._env_prefix = kwargs.get("prefix", env_prefix)
        self._conf_mgr = BaseConfManager(env_file=env_file)
        self._defaults_enable_logger_conf = kwargs.get("defaults_enable_logger_conf")
        self._defaults_logger_conf = kwargs.get("defaults_logger_conf")
        self._defaults_file_logger_conf = kwargs.get("defaults_file_logger_conf")
        self._extra = extra
        self._mandatory_logger_conf = (
            mandatory_logger_conf
            if mandatory_logger_conf is not None
            else {"stdout": {"sink": sys.stdout}, "stderr": {"sink": sys.stderr, "level": "ERROR"}}
        )

    # ------------------------------------------------------------------------------------
    # --- Configuration
    # ------------------------------------------------------------------------------------

    @property
    def enable_logger_conf(self) -> EnableLoggerConf:
        """Retrieve the configuration for enabling or disabling logging."""
        return self._conf_mgr.get_conf(
            conf_type=EnableLoggerConf,
            conf_name="ENABLE_LOGGER_CONF",
            env_prefix=self._env_prefix,
            defaults=self._defaults_enable_logger_conf,
        )

    @property
    def logger_conf(self) -> dict[str, LoggerConf]:
        """Retrieve the logger configurations."""
        return {
            key: self._conf_mgr.get_conf(
                conf_type=LoggerConf,
                conf_name=f"LOGGER_CONF_{key.upper()}",
                env_prefix=self._env_prefix,
                defaults=self._defaults_logger_conf,
                **mandatory,
            )
            for key, mandatory in self._mandatory_logger_conf.items()
        }

    @property
    def file_logger_conf(self) -> FileLoggerConf:
        """Retrieve the file logger configuration."""
        return self._conf_mgr.get_conf(
            conf_type=FileLoggerConf,
            conf_name="FILE_LOGGER_CONF",
            env_prefix=self._env_prefix,
            defaults=self._defaults_file_logger_conf,
        )

    def get_configuration(self, mode: str = "json") -> dict[str, Any]:
        """Returns the current logging configuration.

        Args:
            mode (str): Serialization mode (default: "json").

        Returns:
            dict[str, Any]: Full logging configuration.
        """

        def _serialized_conf(conf: Optional[dict[str, Any]]) -> dict[str, str]:
            _conf = conf or {}
            if mode == "json":
                return {key: str(value) for key, value in _conf.items()}
            return _conf

        return {
            "env_prefix": self._env_prefix,
            "env_file": self._conf_mgr.env_file,
            "defaults_enable_logger_conf": _serialized_conf(self._defaults_enable_logger_conf),
            "defaults_file_logger_conf": _serialized_conf(self._defaults_file_logger_conf),
            "mandatory_logger_conf": _serialized_conf(self._mandatory_logger_conf),
            "extra": self._extra,
            **{key: value.model_dump(mode=mode) for key, value in self._conf_mgr.config_map.items()},
        }

    # ------------------------------------------------------------------------------------
    # --- Logging Initialisation
    # ------------------------------------------------------------------------------------

    def init_logging(self, logger: LoggerType, loggers_to_intercept: Optional[list[str]] = None) -> None:
        """Initialises logging configuration and optionally intercepts specified loggers.

        Args:
            logger (LoggerType): The logger instance to configure.
            loggers_to_intercept (list[str], optional): Optional list of loggers to intercept.
        """
        if loggers_to_intercept:
            self.init_logging_handlers(logger, loggers_to_intercept)
        self.init_logging_conf(logger)

    def init_logging_conf(self, logger: Optional[LoggerType] = None) -> None:
        """Configures the logging settings.

        Args:
            logger (LoggerType, optional): The logger instance to configure.
                If not provided, the default logger obtained from the `get_logger` function will be used.
        """
        _logger: LoggerType = get_logger() if not logger else logger
        enable_logger_conf: EnableLoggerConf = self.enable_logger_conf
        if enable_logger_conf.enable:
            _logger.configure(extra=self._extra)
            _logger.remove()
            _logger._core.handlers_count = 0

            for key, config in self.logger_conf.items():
                if key == "stdout" or (enable_logger_conf.enable_stderr and key == "stderr"):
                    _logger.add(**config.model_dump())

            if enable_logger_conf.enable_file:
                _logger.add(**self.file_logger_conf.model_dump())

            _logger.debug(f"Logger configured: {self.get_configuration()}")

    @classmethod
    def init_logging_handlers(cls, logger: LoggerType, loggers_to_intercept: list[str]) -> None:
        """Intercepts and redirects specified loggers to a structured logger.

        WARNING: If called in the startup event, logs before application start will use the old format.

        Args:
            logger (LoggerType): The structured logger instance.
            loggers_to_intercept (list[str]): List of loggers to intercept.
        """

        for logger_name in loggers_to_intercept:
            for intercepted_logger in (
                logging.getLogger(name)
                for name in logging.root.manager.loggerDict  # pylint:disable=no-member
                if name.startswith(f"{logger_name}.")
            ):
                intercepted_logger.handlers = [InterceptHandler(logger, intercepted_logger.name)]
                intercepted_logger.propagate = False  # Prevent duplicate log messages
            log = logging.getLogger(logger_name)
            log.handlers = [InterceptHandler(logger, logger_name)]
            log.propagate = False  # Prevent duplicate log messages
