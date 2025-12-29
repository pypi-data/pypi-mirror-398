"""Модуль логирования."""

import logging
import sys
from logging.handlers import QueueHandler, QueueListener
from queue import Queue

from weblite_framework.logging.formatters import JsonFormatter

__all__ = [
    'get_logger',
]


_loggers: dict[str, logging.Logger] = {}
_handler: logging.Handler | None = None


def get_handler() -> logging.Handler:
    """Создает и возвращает обработчик логов.

    Обработчик использует очередь и listener для асинхронного логирования
    во всех логгерах.

    Returns:
        logging.Handler: Настроенный обработчик логов
    """
    global _handler

    if _handler is not None:
        return _handler

    log_queue: Queue[logging.LogRecord] = Queue()

    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setFormatter(fmt=JsonFormatter())

    listener = QueueListener(log_queue, stream_handler)
    listener.start()

    _handler = QueueHandler(queue=log_queue)

    return _handler


def get_logger(name: str) -> logging.Logger:
    """Создает и возвращает логгер.

    Логирование происходит в отдельном потоке через QueueHandler.

    Args:
        name: str

    Returns:
        logging.Logger: Настроенный логгер
    """
    if name in _loggers:
        return _loggers[name]

    logger: logging.Logger = logging.getLogger(name=name)
    logger.setLevel(level=logging.INFO)
    logger.addHandler(hdlr=get_handler())

    _loggers[name] = logger

    return logger
