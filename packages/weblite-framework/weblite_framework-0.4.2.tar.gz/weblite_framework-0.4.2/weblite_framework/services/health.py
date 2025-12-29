"""Сервис для проверки работоспособности приложения."""

from sqlalchemy.ext.asyncio import AsyncSession

from weblite_framework.exceptions.service import DatabaseConnectionError
from weblite_framework.repository.common import CommonRepo

__all__ = [
    'HealthService',
]


class HealthService:
    """Сервис для проверки работоспособности приложения."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует сервис.

        Args:
            session: Асинхронная сессия.
        """
        self.__session = session
        self.__repo = CommonRepo(session=self.__session)  # type: ignore

    async def check_db_connection(self) -> None:
        """Проверяет соединение с базой данных.

        В случае отсутствия соединения генерирует ошибку.
        """
        is_connection_exist = await self.__repo._is_connection_exist()
        if not is_connection_exist:
            raise DatabaseConnectionError
