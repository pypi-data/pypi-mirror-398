import logging
import sys
from contextlib import contextmanager
from enum import IntEnum
from functools import cached_property
from logging.handlers import QueueHandler, QueueListener
from multiprocessing import Queue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


class InvalidLogLevelError(ValueError):
    def __init__(self, log_level: str) -> None:
        super().__init__(f"Invalid log level: {log_level}")


class LogLevel(IntEnum):
    NEVER = 100
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG

    @classmethod
    def decode(cls, value: str) -> LogLevel:
        if not value:
            return cls.NEVER
        try:
            return cls[value.upper()]
        except (AttributeError, KeyError) as exc:
            raise InvalidLogLevelError(value) from exc


type ConsoleHandlers = tuple[logging.StreamHandler, logging.StreamHandler]


class LogMeister:
    def __init__(self, main_name: str) -> None:
        self._main_name = main_name

    @cached_property
    def _console_handlers(self) -> ConsoleHandlers:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.addFilter(lambda rec: rec.levelno <= LogLevel.INFO)
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.addFilter(lambda rec: rec.levelno > LogLevel.INFO)
        return stdout_handler, stderr_handler

    def _setup_logger(
        self, *handlers: logging.Handler, level: LogLevel, name: str = None
    ) -> None:
        logger = self.get_logger(name)
        logger.setLevel(level)
        logger.propagate = False
        for handler in handlers:
            logger.addHandler(handler)

    @contextmanager
    def context(self, main_level: LogLevel, **levels: LogLevel) -> Iterator[None]:
        """
        Context manager to activate logging queues.

        >>> log = LogMeister("my-app")
        >>> def foo():
        ...     log.get_logger("warnings").warning("Shouldn't log yet.")
        ...     with log.context(LogLevel.INFO, warnings=LogLevel.WARNING):
        ...         log.get_logger().info("This should show up.")
        ...         log.get_logger("warnings").warning("...this as well.")
        ...         log.get_logger("warnings").info("...but INFO shouldn't.")
        ...     log.get_logger("warnings").warning("Shouldn't log anymore.")
        """
        self._setup_logger(*self._console_handlers, level=main_level)

        if not levels:
            yield
            return

        queue: Queue[logging.LogRecord] = Queue()
        for name, level in levels.items():
            self._setup_logger(
                QueueHandler(queue), level=max(level, main_level), name=name
            )
        queue_listener = QueueListener(queue, *self._console_handlers)
        queue_listener.start()
        try:
            yield
        finally:
            queue_listener.stop()

    def get_logger(self, name: str = None) -> logging.Logger:
        full_name = self._main_name
        if name:
            full_name += f".{name}"
        return logging.getLogger(full_name)

    @cached_property
    def _main_logger(self) -> logging.Logger:
        return self.get_logger()
