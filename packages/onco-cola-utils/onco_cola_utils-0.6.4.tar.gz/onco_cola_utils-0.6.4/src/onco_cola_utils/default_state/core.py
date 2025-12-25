from datetime import datetime
from typing import Generic, Optional, TypeAlias, TypeVar

from pydantic import BaseModel, Field


AllowedTypes: TypeAlias = str | list | int | dict

T = TypeVar('T')


class MetaState(BaseModel):
    """
    Мета-информация о состоянии
    """
    created_at: int = Field(description="Дата-время создания")
    updated_at: int = Field(description="Дата-время последнего обновления")


class DefaultState(BaseModel, Generic[T]):
    """
    Дефолтный ответ вообще для всех существующих методов.

    Attributes:
        result (Optional[bool]): Общий результат выполнения действия
        status (Optional[AllowedTypes]): Короткое воплощение details
        detail (Optional[AllowedTypes]): Текстовое сообщение об ошибке
        data (Optional[T]): Любые данные, которые должны вернуться
        meta (MetaState): Системная мета-информация (id, created_at, updated_at)
    """

    result: Optional[bool] = Field(default=False)
    status: Optional[AllowedTypes] = Field(default='INIT')
    detail: Optional[AllowedTypes] = Field(default='')
    data: Optional[T] = None
    meta: MetaState = Field(
        default_factory=lambda: MetaState(
            created_at=int(datetime.now().timestamp()),
            updated_at=int(datetime.now().timestamp())
        )
    )

    model_config = {
        "use_enum_values": True,
        "arbitrary_types_allowed": True,
    }

    def __init__(self, init_data: Optional[dict] = None, **kwargs) -> None:
        """
        Поддерживает инициализацию:
        - Из словаря: DefaultState({'result': True, ...})
        - Из ключевых аргументов: DefaultState(result=True, ...)
        - Пустую инициализацию: DefaultState()
        """
        # Создаем мета-информацию перед инициализацией
        meta = MetaState(
            created_at=int(datetime.now().timestamp()),
            updated_at=int(datetime.now().timestamp())
        )

        if init_data and isinstance(init_data, dict):
            processed_data = {
                'result': init_data.get('result', False),
                'status': init_data.get('status', 'INIT'),
                'detail': init_data.get('detail', ''),
                'data': init_data.get('data'),
            }
            # Гарантируем, что meta не перезапишется, если передано
            if 'meta' not in kwargs:
                kwargs['meta'] = self.meta
            super().__init__(**processed_data, **kwargs)
        else:
            # kwargs['meta'] = meta
            super().__init__(**kwargs)

    def __bool__(self) -> bool:
        """Позволяет использовать объект в булевом контексте (if/not)"""
        return self.result is True

    def _update_meta(self) -> None:
        """Обновляет время последнего изменения"""
        self.meta.updated_at = int(datetime.now().timestamp())

    def update(
        self: 'DefaultState[T]',
        *,
        result: bool = False,
        status: Optional[AllowedTypes] = None,
        detail: Optional[AllowedTypes] = None,
        data: Optional[T] = None,
    ) -> 'DefaultState[T]':
        """Обновляет данные стейта и мета-поля."""
        if result is not None:
            self.result = result
        if status is not None:
            self.status = status
        if detail is not None:
            self.detail = detail
        if data is not None:
            self.data = data

        self._update_meta()
        return self

    def success(
        self: 'DefaultState[T]',
        *,
        status: Optional[AllowedTypes] = None,
        detail: Optional[AllowedTypes] = None,
        data: Optional[T] = None,
    ) -> 'DefaultState[T]':
        """Устанавливает result=True и обновляет мета-поля."""
        self.result = True
        if status is not None:
            self.status = status
        if detail is not None:
            self.detail = detail
        if data is not None:
            self.data = data

        self._update_meta()
        return self

    def insert(self, data: dict) -> 'DefaultState[T]':
        """Алиас для update с передачей словаря (обратная совместимость)"""
        return self.update(**data)

    @property
    def created_at(self) -> int:
        """Короткий доступ к meta.created_at"""
        return self.meta.created_at

    @property
    def updated_at(self) -> int:
        """Короткий доступ к meta.updated_at"""
        return self.meta.updated_at

    @property
    def created_dt(self) -> datetime:
        """Возвращает created_at как объект datetime"""
        return datetime.fromtimestamp(self.created_at)

    @property
    def updated_dt(self) -> datetime:
        """Возвращает updated_at как объект datetime"""
        return datetime.fromtimestamp(self.updated_at)
