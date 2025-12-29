"""Модуль базового сервиса для работы с бизнес-логикой."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

__all__ = ['BaseServiceClass']

Dataclass = TypeVar('Dataclass')
PydanticSchema = TypeVar('PydanticSchema')


class BaseServiceClass(Generic[Dataclass, PydanticSchema], ABC):
    """Базовый сервис с общими методами."""

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        """Инициализирует базовый сервис.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session

    @abstractmethod
    def _dto_to_schema(
        self,
        dto: Dataclass,
    ) -> PydanticSchema:
        """Конвертирует Dataclass в PydanticSchema.

        Args:
            dto: Объект Dataclass

        Returns:
            PydanticSchema: Объект схемы
        """
        pass

    @abstractmethod
    def _schema_to_dto(
        self,
        schema: PydanticSchema,
    ) -> Dataclass:
        """Конвертирует PydanticSchema в Dataclass.

        Args:
            schema: Объект PydanticSchema

        Returns:
            Dataclass: Объект Dataclass
        """
        pass

    def _bulk_dto_to_schema(
        self,
        dtos: list[Dataclass],
    ) -> list[PydanticSchema]:
        """Конвертирует список Dataclass в список схем PydanticSchema.

        Args:
            dtos: Список объектов Dataclass

        Returns:
            list[PydanticSchema]: Список объектов схемы
        """
        schemas: list[PydanticSchema] = []
        for dto in dtos:
            schema = self._dto_to_schema(dto)
            schemas.append(schema)
        return schemas

    def _bulk_schema_to_dto(
        self,
        schemas: list[PydanticSchema],
    ) -> list[Dataclass]:
        """Конвертирует список PydanticSchema в список Dataclass.

        Args:
            schemas: Список объектов схемы

        Returns:
            list[Dataclass]: Список объектов Dataclass
        """
        dtos: list[Dataclass] = []
        for schema in schemas:
            dto = self._schema_to_dto(schema)
            dtos.append(dto)
        return dtos
