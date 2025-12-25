# Tools

Утилитарный класс с коллекцией статических методов для обработки строк, работы с данными, файлами и текстовыми операциями. Содержит более 50 специализированных методов для различных задач.

## Особенности

- **📝 Обработка строк** — нормализация, очистка, поиск, трансформация
- **🔧 Работа с данными** — фильтрация, сортировка, разбиение на чанки
- **📁 Файловые операции** — поиск, фильтрация, очистка директорий
- **🎯 Специализированные методы** — для задач разметки товарных карточек
- **⚡ Производительность** — оптимизированные алгоритмы для больших объемов данных

## Установка

```python
# Класс требует установки дополнительных зависимостей
pip install tiktoken

# Импорт в проект
from tools import Tools
```

## Основные категории методов

### Обработка строк

#### `clean_field(string: str) -> str`
Комплексная очистка строки от лишних пробелов и спецсимволов.

```python
Tools.clean_field("  Hello,,  World!  ")  # "Hello, World!"
```

#### `string_stripper(text: str) -> str`
Удаляет все типы Unicode-пробелов и схлопывает множественные пробелы.

```python
Tools.string_stripper("Hello\u200B\u200BWorld")  # "Hello World"
```

#### `get_dry_string(input_string: str, allows: str = None) -> str`
Оставляет только буквы, цифры и разрешенные символы в lower-формате.

```python
Tools.get_dry_string("iPhone 14 Pro Max!")  # "iphone14promax"
Tools.get_dry_brand("SAMSUNG-Galaxy")       # "samsung-galaxy"
```

#### `polysplit(text: str, separators: list = None, no_empty: bool = False) -> list[str]`
Разбивает строку по нескольким разделителям.

```python
Tools.polysplit("apple/orange|banana")  # ['apple', 'orange', 'banana']
```

### Работа с текстом

#### `find_original_substring(source: str, word: str) -> Optional[str]`
Находит подстроку в исходном регистре по образцу в нижнем регистре.

```python
source = "Стиральная машина AEG L7WBE68SI"
Tools.find_original_substring(source, "aeg")  # "AEG"
```

#### `ireplace(string: str, substr: str, value: str = "") -> str`
Заменяет подстроку без учета регистра.

```python
Tools.ireplace("Hello World world", "WORLD", "")  # "Hello "
```

#### `remove_duplicate_words(text: str) -> str`
Удаляет повторяющиеся слова, сохраняя порядок.

```python
Tools.remove_duplicate_words("hello hello world world")  # "hello world"
```

### Фильтрация и поиск

#### `get_dict_filtered(data: dict, include_by_rules: list[dict], strict: bool = False) -> dict`
Фильтрует словарь словарей по сложным правилам.

```python
data = {1: {'status': 'active', 'cat': 'A'}, 2: {'status': 'pending', 'cat': 'B'}}
rules = [{'status': 'active'}, {'cat': 'A'}]
Tools.get_dict_filtered(data, rules)  # {1: {'status': 'active', 'cat': 'A'}}
```

#### `ifound(string: str, substring: str, is_all: bool = False) -> bool | list[int]`
Регистронезависимый поиск с возвратом позиций.

```python
Tools.ifound("Hello World", "world")        # True
Tools.ifound("Hello world", "o", True)      # [4, 7]
```

### Работа с коллекциями

#### `no_repeats_of_list(lst: list) -> list`
Удаляет дубликаты с сохранением порядка.

```python
Tools.no_repeats_of_list([1, 3, 2, 1, 3])  # [1, 3, 2]
```

#### `sequential_combinations(words_list: list[str], use_dry: bool = True, get_string: bool = True)`
Генерирует последовательные комбинации слов.

```python
Tools.sequential_combinations(["apple", "iphone", "14"])  
# ["apple iphone 14", "apple iphone", "iphone 14", ...]
```

#### `filter_list(a: list, b: list) -> list`
Оставляет в списке A только элементы, которых нет в B.

```python
Tools.filter_list([1, 2, 3, 4], [2, 4])  # [1, 3]
```

### Распределение данных

#### `get_threads_data_parts_by_dict(idfy_not_null_dict: IdfyGoods, thread_pks: list[int], ...) -> IndexedIdfyGoods`
Распределяет данные между потоками.

```python
data = {1: {...}, 2: {...}, ... 99: {...}}
threads = [101, 102, 103]
Tools.get_threads_data_parts_by_dict(data, threads)
# {101: {1:..., 2:...}, 102: {3:..., 4:...}, 103: {5:..., 6:...}}
```

#### `get_chunks_data_by_dict(idfy_not_null_dict: dict, chunk_size: int) -> list[dict]`
Делит словарь на чанки фиксированного размера.

```python
data = {1: {...}, 2: {...}, ... 100: {...}}
Tools.get_chunks_data_by_dict(data, 10)  # [{1-10: ...}, {11-20: ...}, ...]
```

### Файловые операции

#### `get_all_files_from_dir(dir_path: Path, exts_list: list = None, exclude_file_with_list: list = None) -> list[Path]`
Собирает файлы из директории с фильтрацией.

```python
files = Tools.get_all_files_from_dir(
    Path("/data"), 
    exts_list=['xlsx', 'csv'],
    exclude_file_with_list=['temp', 'backup']
)
```

#### `clear_directory_contents(path: Path, with_dir: bool = False) -> None`
Рекурсивно очищает содержимое директории.

```python
Tools.clear_directory_contents(Path("/tmp/processing"))
```

### Специализированные методы для разметки

#### `get_all_fields(fields: list[str]) -> list[str]`
Добавляет суффиксы `_asis` и `_tobe` к полям.

```python
Tools.get_all_fields(['entity', 'brand'])  
# ['entity_asis', 'entity_tobe', 'brand_asis', 'brand_tobe']
```

#### `get_relay(fields: list[str]) -> dict[str, str]`
Создает маппинг asis→tobe полей.

```python
Tools.get_relay(['entity', 'brand'])  
# {'entity_asis': 'entity_tobe', 'brand_asis': 'brand_tobe'}
```

#### `completely_nulled(fields: list[str], data_dict: dict) -> bool`
Проверяет, что все указанные поля равны "0".

```python
Tools.completely_nulled(['entity_tobe', 'brand_tobe'], data)  # True/False
```

### Валидация и парсинг

#### `is_valid_json(s) -> bool`
Проверяет валидность JSON строки.

```python
Tools.is_valid_json('{"name": "test"}')  # True
```

#### `def parse_filename(filename: str, is_filters: bool = False) -> tuple[int, str]:`
Парсит имена файлов формата "2417_Лестницы_и_стремянки_20250529_на_разметку.xlsx", а также "Фильтры_2417_Лестницы_и_стремянки_20250529_на_разметку.xlsx", если установлен флаг `is_filters=True`

```python
Tools.parse_filename("2417_Лестницы_20250529_на_разметку.xlsx")  
# (2417, "Лестницы")

Tools.parse_filename("Фильтры_2417_Лестницы_20250529_на_разметку.xlsx", is_filters=True)  
# (2417, "Лестницы")
```

### Утилиты

#### `num_tokens_from_messages(messages, model="gpt-4o-mini") -> int`
Подсчитывает количество токенов для OpenAI моделей.

```python
messages = [{"role": "user", "content": "Hello"}]
Tools.num_tokens_from_messages(messages)  # 15
```

#### `try_to_int(data) -> bool`
Безопасно проверяет, можно ли преобразовать данные в int.

```python
Tools.try_to_int("123")  # True
Tools.try_to_int("abc")  # False
```

## Примеры использования

### Обработка названий товаров

```python
def normalize_product_name(name: str) -> str:
    """Нормализация названия товара для поиска"""
    name = Tools.clean_field(name)
    name = Tools.ireplace(name, "official", "")
    name = Tools.remove_duplicate_words(name)
    return Tools.get_dry_string(name)

product_name = "Apple  iPhone  14 Pro  Max Official"
normalized = normalize_product_name(product_name)  # "appleiphone14promax"
```

### Фильтрация данных для обработки

```python
def prepare_data_for_processing(data: IdfyGoods) -> IdfyGoods:
    """Подготовка данных для нейросети"""
    # Фильтруем только активные записи
    filtered = Tools.get_dict_filtered(
        data, 
        [{'status': 'active'}, {'remark': '1'}]
    )
    
    # Убираем полностью нулевые записи
    return {
        id: item for id, item in filtered.items()
        if not Tools.completely_nulled(['entity_tobe', 'brand_tobe'], item)
    }
```

### Пакетная обработка файлов

```python
def process_category_files(category_dir: Path) -> list[tuple]:
    """Обработка всех файлов категории"""
    files = Tools.get_all_files_from_dir(
        category_dir, 
        exts_list=['xlsx'],
        exclude_file_with_list=['backup']
    )
    
    categories = []
    for file in files:
        try:
            cat_id, cat_name = Tools.parse_filename(file.name)
            categories.append((cat_id, cat_name, file))
        except ValueError as e:
            print(f"Ошибка парсинга {file.name}: {e}")
    
    return categories
```

## Зависимости

- **tiktoken** — подсчет токенов для OpenAI
- **re** — регулярные выражения
- **json** — работа с JSON
- **pathlib** — работа с путями
- **shutil** — файловые операции

## Особенности производительности

- Все методы статические — не требуют создания экземпляра
- Оптимизированы для работы с большими объемами данных
- Минимальное потребление памяти при потоковой обработке
- Эффективные алгоритмы поиска и фильтрации