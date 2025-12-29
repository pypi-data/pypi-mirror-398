"""Модуль исключений, связанных с авторизацией и правами доступа."""

from weblite_framework.exceptions.base import BaseAppException

__all__ = [
    'UnauthorizedException',
    'ForbiddenException',
]


class UnauthorizedException(BaseAppException):
    """Класс исключения, связанного с авторизацией."""

    def __init__(self, detail: str = 'Необходима авторизация') -> None:
        """Инициализирует исключение при отсутствии авторизации.

        Args:
            detail: Сообщение с передаваемой информацией
        """
        super().__init__(
            status_code=401,
            detail=detail,
        )


class ForbiddenException(BaseAppException):
    """Класс исключения, вызываемого при отсутствии прав доступа к ресурсу."""

    def __init__(
        self,
        detail: str = 'Доступ запрещён. У вас нет прав на выполнение данного '
        'действия.',
    ) -> None:
        """Инициализирует исключение при отсутствии прав доступа.

        Args:
            detail: Сообщение с передаваемой информацией
        """
        super().__init__(
            status_code=403,
            detail=detail,
        )
