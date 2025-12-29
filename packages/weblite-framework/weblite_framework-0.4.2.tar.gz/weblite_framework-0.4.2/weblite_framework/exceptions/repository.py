"""Модуль исключений, связанных с ошибками в слое репозитория."""

from weblite_framework.exceptions.base import BaseAppException

__all__ = [
    'RepositoryException',
]


class RepositoryException(BaseAppException):
    """Класс исключения, связанного с БД."""

    def __init__(
        self,
        detail: str = 'Ошибка при работе с репозиторием',
    ) -> None:
        """Инициализирует исключение, возникшее в слое репозитория.

        Args:
            detail: Сообщение с передаваемой информацией
        """
        super().__init__(
            status_code=500,
            detail=detail,
        )
