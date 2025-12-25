# value_to_bool

Функция `value_to_bool` предоставляет надежный способ преобразования различных типов значений (строк, чисел, булевых) в булево значение, используя расширенный набор правил.

#### Функция `value_to_bool`

```python
value_to_bool(value: Any) -> bool
```

-   `value`: Любое значение, которое нужно преобразовать в булево.

**Правила преобразования:**

-   **`True`**: `True`, `1`, `"true"`, `"1"`, `"yes"`, `"on"`, `"+"`, `"ok"`, `"да"`, `"вкл"`, `"y"`, `"t"`, `"enable"`, `"enabled"` (регистронезависимо).
-   **`False`**: `False`, `0`, `None`, `""` (пустая строка), `" "` (строка из пробелов), `"false"`, `"0"`, `"no"`, `"off"`, `"-"`, `"нет"`, `"выкл"`, `"n"`, `"f"`, `"disable"`, `"disabled"`, `"null"`, `"none"` (регистронезависимо).
-   Числа с плавающей точкой: `0.0` -> `False`, любое другое число -> `True`.
-   Любое другое значение, которое не соответствует правилам `True` или `False`, будет преобразовано в `False`.

**Пример:**

```python
from onco_cola_utils.value_to_bool import value_to_bool

print(value_to_bool("true"))    # True
print(value_to_bool(1))         # True
print(value_to_bool("да"))      # True
print(value_to_bool("false"))   # False
print(value_to_bool(0))         # False
print(value_to_bool(None))      # False
print(value_to_bool(""))        # False
print(value_to_bool("random_text")) # False
```