"""Модуль с базовыми классами исключений."""

__all__ = [
    'BaseAppException',
]


class BaseAppException(Exception):
    """Базовое исключение для всех кастомных исключений."""

    def __init__(self, status_code: int, detail: str) -> None:
        """Инициализирует базовое исключение.

        Args:
            status_code: Код передаваемой ошибки
            detail: Сообщение с передаваемой информацией
        """
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.detail)
