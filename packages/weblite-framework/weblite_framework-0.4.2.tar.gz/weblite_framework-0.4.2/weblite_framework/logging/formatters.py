"""Модуль с форматтерами для логирования."""

import json
import logging
from datetime import datetime

__all__ = [
    'JsonFormatter',
]


class JsonFormatter(logging.Formatter):
    """Класс для преобразования записей логов в JSON-строки с полями."""

    def format(self, record: logging.LogRecord) -> str:
        """Форматирует запись лога в JSON строку.

        Поля:
        timestamp: Временная метка
        level: Уровень логирования
        source: Источник сообщения (модуль)
        message: Текст сообщения

        Args:
            record: Запись лога для форматирования

        Returns:
              JSON-строка с отформатированным логом
        """
        log_record = {
            'timestamp': datetime.fromtimestamp(record.created)
            .astimezone()
            .isoformat(),
            'level': record.levelname,
            'source': record.module,
            'message': record.getMessage(),
        }
        return json.dumps(
            obj=log_record,
            ensure_ascii=False,
        )
