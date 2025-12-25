
# pretty_print

Модуль `pretty_print` предоставляет функцию для форматированного вывода сложных структур данных, таких как `dataclasses`, словари и списки. Это значительно улучшает читаемость вывода в консоли и упрощает отладку.

#### Функция `pretty_print`

```python
pretty_print(obj, indent: int = 4, title: str = 'PRETTY_PRINT', m2d: bool = False, outputter=log)
```

-   `obj`: Объект, который нужно вывести. Может быть `dataclass`, словарем, списком или другим типом.
-   `indent` (`int`, по умолчанию `4`): Количество пробелов для каждого уровня отступа.
-   `title` (`str`, по умолчанию `'PRETTY_PRINT'`): Заголовок, который будет выведен перед форматированным объектом.
-   `m2d` (`bool`, по умолчанию `False`): Если `True`, функция попытается преобразовать объект в словарь с помощью `model_to_dict` перед форматированием. Это полезно для объектов ORM или других моделей, которые могут быть преобразованы в словари.
-   `outputter` (`callable`, по умолчанию `log`): Функция, которая будет использоваться для вывода строк. По умолчанию используется функция `log` из встроенного модуля `logger`.

**Пример:**

```python
from dataclasses import dataclass
from onco_cola_utils.pretty_print.core import pretty_print

@dataclass
class User:
    name: str
    age: int
    contacts: dict

user_data = User(
    name="Alice",
    age=30,
    contacts={
        "email": "alice@example.com",
        "phone": "123-456-7890"
    }
)

pretty_print(user_data, title="User Profile")

# Вывод:
# User Profile
# User(
#     name='Alice',
#     age=30,
#     contacts={
#         'email': 'alice@example.com',
#         'phone': '123-456-7890',
#     },
# )

pretty_print({"item1": 10, "item2": ["a", "b"]}, title="My Dictionary")

# Вывод:
# My Dictionary
# dict(
#     'item1': 10,
#     'item2': [
#         'a',
#         'b',
#     ],
# )
```