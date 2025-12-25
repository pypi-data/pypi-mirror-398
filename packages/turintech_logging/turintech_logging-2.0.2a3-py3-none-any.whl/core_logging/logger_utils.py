# ───────────────────────────────────────────────────── imports ────────────────────────────────────────────────────── #
import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from typing_extensions import TypeAlias

if TYPE_CHECKING:
    import loguru

    LoggerType: TypeAlias = loguru.Logger
else:
    LoggerType: TypeAlias = Any

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#         Defines the public interface of the module that will be imported when using 'from package import *'.         #
#    This helps control what is exposed to the global namespace, limiting imports to only those listed in __all__.     #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #

__all__ = [
    "LoggerType",
    "is_logger_instance",
    "get_logger",
    "get_logging_backup",
    "set_logging_buckup",
    "get_loguru_backup",
    "set_loguru_buckup",
    "preserve_logging_state",
]


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #
#                                                Module Implementation                                                 #
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── #


def get_logger(**bind_args) -> LoggerType:
    """Returns a logger instance, optionally binding extra context.

    The import of the loguru logger instance is done inside this function to prevent
    serialization issues.

    Args:
        **bind_args: The arguments to bind additional context to the logger.

    Returns:
        LoggerType: A logger instance with the provided context bound to it.
    """
    from loguru import logger  # pylint: disable=import-outside-toplevel

    return logger.bind(**bind_args)


def is_logger_instance(obj: object) -> bool:
    """Check whether an object behaves like a logger.

    This validates the minimal logging interface required by the application,
    without coupling to a concrete logger implementation.
    """
    required_methods = (
        "debug",
        "info",
        "warning",
        "error",
        "exception",
    )

    return all(callable(getattr(obj, method, None)) for method in required_methods)


# ------------------------------------------------------------------------------------
# --- Preserve and restore the state of loggers
# ------------------------------------------------------------------------------------


def get_logging_backup() -> dict[str, dict[str, Any]]:
    """Returns a dictionary containing the state of the logging module.

    Returns:
        dict[str, dict[str, Union[bool, list[logging.Handler]]]]: A dictionary containing the state
            of the logging module.
    """
    return {
        name: {
            "handlers": list(logger.handlers),
            "propagate": logger.propagate,
        }
        for name, logger in [(logging.root.name, logging.root.handlers)] + list(logging.root.manager.loggerDict.items())
        if isinstance(logger, logging.Logger)
    }


def set_logging_buckup(logging_backup: dict[str, dict[str, Any]]) -> None:
    """Restore the state of the logging module from a backup.

    Args:
        logging_backup (dict[str, dict[str, Union[bool, list[logging.Handler]]]]): The backup dictionary
            created by get_logging_backup().
    """
    for name, logger in [(logging.root.name, logging.root.handlers)] + list(logging.root.manager.loggerDict.items()):
        if isinstance(logger, logging.Logger):
            if state := logging_backup.get(name):
                logger.handlers = state["handlers"]
                logger.propagate = state["propagate"]
            else:
                logging.root.manager.loggerDict.pop(name, None)


def get_loguru_backup() -> dict[str, Any]:
    """Returns a dictionary containing the state of the loguru logger.

    Returns:
        dict[str, Any]: A dictionary containing the state of the loguru logger.
    """
    from loguru import logger
    from loguru._logger import Core

    _core: Core = logger._core  # pyright: ignore[reportAttributeAccessIssue]
    return {
        **_core.__getstate__(),
        "enabled": _core.enabled.copy(),
        "handlers": _core.handlers.copy(),
    }


def set_loguru_buckup(loguru_backup: dict[str, Any]) -> None:
    """Restore the state of loguru logger from a backup.

    Args:
        loguru_backup (dict[str, Any]): The backup dictionary created by get_loguru_backup().

    Warning:
        The colorize argument is not restored, so the color of the logger might not be the same as before.
    """
    from loguru import logger
    from loguru._file_sink import FileSink
    from loguru._logger import Core
    from loguru._simple_sinks import StreamSink

    _core: Core = logger._core  # pyright: ignore[reportAttributeAccessIssue]

    # Remove all handlers currently added to the logger
    logger.remove()
    _core.handlers_count = 0

    # Restore the internal state of the logger (except handlers)
    handlers_backup = loguru_backup.get("handlers", {})
    _core.__setstate__(
        {key: value for key, value in loguru_backup.items() if key not in ["handlers", "handlers_count"]}
    )

    # Add each handler again using logger.add()
    for _id, handler in handlers_backup.items():
        fmt_with_exc = handler._formatter.strip()
        fmt = fmt_with_exc[: -len("\n{exception}")] if fmt_with_exc.endswith("\n{exception}") else fmt_with_exc

        sink = (
            handler._sink._stream
            if isinstance(handler._sink, StreamSink)
            else handler._sink._path
            if isinstance(handler._sink, FileSink)
            else handler._sink
        )

        logger.add(
            sink=sink,
            level=handler._levelno,
            format=fmt,
            filter=handler._filter,
            serialize=handler._serialize,
            enqueue=handler._enqueue,
            context=handler._multiprocessing_context,
            catch=handler._error_interceptor._should_catch,
        )


@contextmanager
def preserve_logging_state():
    """Context manager to temporarily preserve and restore the state of loggers."""
    logging_backup = get_logging_backup()
    loguru_backup = get_loguru_backup()
    try:
        yield
    finally:
        set_logging_buckup(logging_backup)
        set_loguru_buckup(loguru_backup)
