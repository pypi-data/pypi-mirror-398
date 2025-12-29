"""Модуль проверки соединения БД."""

from typing import TypeVar

from weblite_framework.database.models import BaseModel
from weblite_framework.repository.base import BaseRepositoryClass

__all__ = [
    'CommonRepo',
]

DTO = TypeVar('DTO')
SQLModel = TypeVar(
    'SQLModel',
    bound=BaseModel,
)


class CommonRepo(BaseRepositoryClass[DTO, SQLModel]):
    """Класс для проверки соединения БД."""

    def _model_to_dto(self, model: SQLModel) -> DTO:
        """Метод-заглушка.

        Этот метод является заглушкой для поддержки наследования
        классов от базового, но не предназначен для использования
        внутри этого класса.
        """
        raise NotImplementedError(
            'Данный метод не поддерживается в этом классе',
        )

    def _dto_to_model(self, dto: DTO) -> SQLModel:
        """Метод-заглушка.

        Этот метод является заглушкой для поддержки наследования
        классов от базового, но не предназначен для использования
        внутри этого класса.
        """
        raise NotImplementedError(
            'Данный метод не поддерживается в этом классе',
        )
