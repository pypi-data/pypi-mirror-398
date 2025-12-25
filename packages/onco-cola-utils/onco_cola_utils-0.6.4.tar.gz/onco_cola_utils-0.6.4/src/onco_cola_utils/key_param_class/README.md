# KeyParamClass

`KeyParamClass` — это базовый класс, который позволяет создавать неизменяемые, типобезопасные константы, похожие на `Enum`, но с дополнительными атрибутами `name` (короткое строковое имя) и `desc` (подробное описание). Это удобно для определения фиксированных наборов значений, таких как статусы, типы или категории, где помимо самого значения требуется и его человекочитаемое описание.

#### Использование

Для создания набора констант, унаследуйте свой класс от `KeyParamClass` и определите константы как кортежи `(name: str, desc: str)`.

```python
from onco_cola_utils.key_param_class.core import KeyParamClass

class Status(KeyParamClass):
    PENDING = ("pending", "Ожидает обработки")
    ACTIVE = ("active", "Активен")
    COMPLETED = ("completed", "Завершено")
    CANCELLED = ("cancelled", "Отменено")

# Доступ к константам
print(Status.PENDING)          # Вывод: pending (возвращает .name по умолчанию)
print(Status.ACTIVE.name)      # Вывод: active
print(Status.COMPLETED.desc)   # Вывод: Завершено

# Сравнение
print(Status.PENDING == "pending") # Вывод: True
print(Status.ACTIVE == Status.ACTIVE) # Вывод: True

# Итерация по всем константам
for status in Status:
    print(f"Имя: {status.name}, Описание: {status.desc}")

# Получение константы по имени или атрибуту
print(Status.from_name("active")) # Вывод: <Status.ACTIVE: active (Активен)>
print(Status.get("COMPLETED"))    # Вывод: <Status.COMPLETED: completed (Завершено)>

# Получение всех констант в виде списка кортежей (name, desc)
print(Status.choices) # Вывод: [("pending", "Ожидает обработки"), ("active", "Активен"), ...]

# Получение всех констант в виде словаря
print(Status.dict()) # Вывод: {"PENDING": {"name": "pending", "desc": "Ожидает обработки"}, ...}
```

#### Особенности

-   **Неизменяемость**: После создания экземпляры `KeyParamClass` и сам класс являются неизменяемыми. Попытка изменить их атрибуты вызовет `AttributeError`.
-   **Проверка дубликатов**: Метакласс проверяет уникальность `name` (кода) при определении констант. Дубликаты `desc` (описания) вызовут предупреждение, но не ошибку.
-   **Enum-like API**: Поддерживает методы, схожие с `Enum`, такие как итерация, доступ по ключу (`Status["PENDING"]`), `get()`, `from_name()`, `choices` и `dict()`.

---