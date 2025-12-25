from __future__ import annotations

import warnings
from typing import Any, Generic, Iterator, Optional, TypeVar

_T = TypeVar("_T", bound="KeyParamClass")


class KeyParamClassMeta(type):
    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> KeyParamClassMeta:
        # Собираем новые элементы из текущего класса (не из родителей)
        members: dict[str, tuple[str, str]] = {}
        for key, value in namespace.items():
            if isinstance(value, (tuple, list)) and len(value) == 2:
                code, description = value
                if not isinstance(code, str) or not isinstance(description, str):
                    raise ValueError(f"Value for {key} must be (str, str)")
                members[key] = (code, description)

        # Создаём класс
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        # Собираем все элементы, включая родительские
        _choices: dict[str, KeyParamClass] = {}
        _by_name: dict[str, KeyParamClass] = {}
        _by_desc: set[str] = set()

        # Наследуем из родителей
        for base in reversed(bases):
            if hasattr(base, "_choices"):
                _choices.update(base._choices)
                _by_name.update(base._by_name)
                _by_desc.update(
                    desc for obj in base._choices.values() if hasattr(obj, "desc") for desc in
                    [obj.desc]
                )

        # Добавляем свои элементы
        for attr_name, (code, description) in members.items():
            if code in _by_name:
                raise ValueError(f"Duplicate name '{code}' in {cls.__name__}")
            if description in _by_desc:
                warnings.warn(
                    f"Duplicate description '{description}' in {cls.__name__}", stacklevel=2
                )

            obj = KeyParamClass(attr_name, code, description)
            setattr(cls, attr_name, obj)
            _choices[attr_name] = obj
            _by_name[code] = obj
            _by_desc.add(description)

        # Присваиваем атрибуты классу
        cls._choices = _choices
        cls._by_name = _by_name
        cls._choices_list = [(obj.name, obj.desc) for obj in _choices.values()]
        cls.__members__ = _choices  # Для совместимости с Enum-like API

        # Запрещаем изменение после создания
        def __setattr__(self, key: str, value: Any) -> None:
            raise AttributeError(f"Cannot modify '{cls.__name__}': it is immutable.")

        cls.__setattr__ = __setattr__

        return cls

    def __iter__(cls) -> Iterator[KeyParamClass]:
        return iter(cls._choices.values())

    def __len__(cls) -> int:
        return len(cls._choices)

    def __getitem__(cls, key: str) -> KeyParamClass:
        return cls._choices[key]

    def get(cls: type[_T], attr_name: str) -> Optional[_T]:
        return cls._choices.get(attr_name)

    def from_name(cls: type[_T], name: str) -> Optional[_T]:
        return cls._by_name.get(name)

    def dict(cls) -> dict[str, dict[str, str]]:
        return {
            key: {"name": obj.name, "desc": obj.desc}
            for key, obj in cls._choices.items()
        }

    @property
    def choices(cls) -> list[tuple[str, str]]:
        return cls._choices_list


class KeyParamClass(Generic[_T], metaclass=KeyParamClassMeta):
    """
    Базовый класс для создания текстовых констант с .name и .desc.
    Пример:
        class Status(KeyParamClass):
            PENDING = ("pending", "Pending")
            ACTIVE = ("active", "Active")

        print(Status.PENDING)          # "pending"
        print(Status.PENDING.name)     # "pending"
        print(Status.PENDING.desc)     # "Active"
        print(Status.choices)          # [("pending", "Pending"), ...]
        Status.from_name("pending")    # -> Status.PENDING
        Status.get("PENDING")          # -> Status.PENDING
        Status.dict()                  # -> {"PENDING": {"name": "...", "desc": "..."}}
    """
    __slots__ = ("_attr_name", "_name", "_desc")

    def __init__(self, attr_name: str, name: str, desc: str) -> None:
        object.__setattr__(self, "_attr_name", attr_name)
        object.__setattr__(self, "_name", name)
        object.__setattr__(self, "_desc", desc)

    def __str__(self) -> str:
        return self._name

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}.{self._attr_name}: {self._name} ({self._desc})>"

    @property
    def name(self) -> str:
        return self._name

    @property
    def desc(self) -> str:
        return self._desc

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, KeyParamClass):
            return self._name == other._name
        return self._name == other

    def __hash__(self) -> int:
        return hash(self._name)

    # Запрещаем изменение экземпляра
    def __setattr__(self, key: str, value: Any) -> None:
        raise AttributeError(f"{self.__class__.__name__} is immutable.")

    def __delattr__(self, item: str) -> None:
        raise AttributeError(f"{self.__class__.__name__} is immutable.")
