# ReaderController

Универсальный контроллер для управления Excel-файлами с поддержкой автоматической валидации, трансформации данных и работы с разметкой товарных карточек.

## Особенности

- **📊 Умное чтение Excel** — автоматическое определение корректного листа с данными
- **🔄 Двойная система идентификации** — порядковая нумерация и local_id
- **🔍 Валидация данных** — проверка структуры, обязательных полей и целостности
- **⚡ Фильтрация и трансформация** — работа с нулевыми значениями, asis/tobe полями
- **📝 Безопасная запись** — проверка блокировки файлов и атомарные операции
- **🎯 Специализированные методы** — для задач разметки товарных карточек

## Установка

```bash
# Установите зависимости
pip install pandas openpyxl deprecated

# Скопируйте модуль в ваш проект
# reader_controller/
#   ├── core.py
#   ├── types.py
#   └── exceptions.py
```

## Быстрый старт

> **Важно:** Перед запуском скриптов, работающих с Excel-файлами, убедитесь, что эти файлы не открыты в других программах, чтобы избежать ошибок доступа (`PermissionError`).

---

### Базовое использование

```python
from pathlib import Path
from reader_controller.core import ReaderController

# Инициализация контроллера
controller = ReaderController(
    file_path=Path("data.xlsx"),
    file_output=Path("output.xlsx"),
    debug=True
)

# Автоматический поиск корректного листа
controller.cycle_right_sheet()

# Чтение данных
controller.read_data()
data = controller.get_data()

print(f"Загружено строк: {controller.rows_data}")
print(f"Всего строк: {controller.rows_total}")
```

### Работа с разметкой товаров

```python
# Получение только значимых данных (исключая нулевые значения)
perfect_data = controller.perfect_data(controller.get_data())

# Получение данных для переразметки
remark_data = controller.get_data_for_remark(perfect_data)

# Работа с полями разметки
asis_fields = controller.get_asis_fields()    # Поля "как есть"
tobe_fields = controller.get_tobe_fields()    # Поля "должно быть"
all_fields = controller.get_all_fields()      # Все поля разметки
```

## API Reference

### Конструктор

#### `ReaderController(file_path: Path, file_output: Path, is_new: bool = False, skip_rows: int = 0, debug: bool = False)`

Создает экземпляр контроллера для работы с Excel-файлами.

**Параметры:**
- `file_path` — путь к исходному Excel-файлу
- `file_output` — путь для сохранения результатов
- `is_new` — файл новый (не требует проверки существования)
- `skip_rows` — количество пропускаемых строк
- `debug` — режим отладки с подробным логированием

**Исключения:**
- `FileNotFoundError` — если файл не существует и `is_new=False`
- `PermissionError` — если файл заблокирован для записи

### Основные методы

#### `read_data(sheet_name: Optional[str] = None)`
Читает данные из указанного листа или автоматически определяет лист.

#### `get_data(sheet_name: Optional[str] = None) -> DFType`
Возвращает данные, при необходимости предварительно загружая их.

#### `filtered_data() -> DFType`
Возвращает данные, отфильтрованные по нулевым значениям.

#### `update_file(same_file: bool = True) -> bool`
Сохраняет изменения в файл.

#### `check_local_id(find_it: bool = True) -> bool`
Проверяет наличие поля `local_id` в данных.

### Методы идентификации данных

#### `local_idfy(data_list: DFType) -> IdfyGoods`
Создает словарь с идентификацией по `local_id`.

```python
data = controller.get_data()
idfy_data = controller.local_idfy(data)
# {1: {'local_id': 1, 'source_name': '...'}, 2: {...}}
```

#### `idfy_to_dataframe(idfy_data: IdfyGoods) -> DFType`
Преобразует idfy-данные обратно в формат списка словарей.

### Методы валидации и фильтрации

#### `perfect_data(data_list: DFType) -> IdfyGoods`
Возвращает только ненулевые строки (где `entity_tobe` не равен "0").

#### `get_data_for_remark(data_dict: dict) -> dict`
Возвращает данные, помеченные для переразметки (`remark == "1"`).

#### `response_validator_substr(data_response: list[dict], validated_fields: list[str], is_ignore: bool = False, filled: bool = False) -> list[dict]`
Валидирует ответы нейросети на соответствие исходным данным.

### Методы работы с файловой системой

#### `cycle_right_sheet() -> None`
Автоматически находит лист с корректной структурой (содержит `source_name` и `url`).

#### `process_local_idfying(field: str = ColumnStrings.DATA_LOCAL_ID)`
Добавляет `local_id` в данные, если его нет.

#### `rename(new_name: str, same_file: bool = True) -> bool`
Переименовывает файл.

### Свойства

#### `rows_total: int`
Общее количество строк (включая заголовок).

#### `rows_data: int`
Количество строк с данными (без заголовка).

#### `dataframe: list[dict]`
Текущий датафрейм с данными.

## Расширенные сценарии использования

### Автоматическая обработка входящих файлов

```python
def process_incoming_file(file_path: Path) -> None:
    """Автоматическая обработка входящего Excel-файла"""
    controller = ReaderController(
        file_path=file_path,
        file_output=file_path.with_stem(f"{file_path.stem}_processed"),
        debug=True
    )
    
    # Автоматический поиск корректного листа
    controller.cycle_right_sheet()
    
    # Проверка и добавление local_id при необходимости
    if not controller.check_local_id():
        controller.process_local_idfying()
    
    # Чтение и фильтрация данных
    controller.read_data()
    perfect_data = controller.perfect_data(controller.get_data())
    
    # Сохранение результата
    controller.override_dataframe(list(perfect_data.values()), is_hard=True)
    controller.update_file(same_file=False)
```

### Обновление данных из внешнего источника

```python
def update_from_external_response(controller: ReaderController, api_response: list[dict]) -> None:
    """Обновление данных на основе ответа API"""
    
    # Валидация ответа
    validated_data = controller.response_validator_substr(
        data_response=api_response,
        validated_fields=['entity_tobe', 'brand_tobe', 'model_tobe'],
        is_ignore=False
    )
    
    # Преобразование в idfy формат
    updated_idfy = {
        int(item['ID']): item for item in validated_data
    }
    
    # Обновление основного датафрейма
    controller.update_dataframe_from_updated_dataframe(
        updated_dataframe=updated_idfy,
        updated_fields=['entity_tobe', 'brand_tobe', 'model_tobe']
    )
    
    # Сохранение изменений
    controller.update_file()
```

### Пакетная обработка файлов

```python
from pathlib import Path

def batch_process_excel_files(input_dir: Path, output_dir: Path) -> None:
    """Пакетная обработка Excel-файлов в директории"""
    
    for excel_file in input_dir.glob("*.xlsx"):
        try:
            output_file = output_dir / f"processed_{excel_file.name}"
            
            controller = ReaderController(
                file_path=excel_file,
                file_output=output_file,
                debug=False
            )
            
            # Основной процесс обработки
            controller.cycle_right_sheet()
            controller.read_data()
            
            if not controller.check_local_id():
                controller.process_local_idfying()
            
            # Фильтрация и сохранение
            perfect_data = controller.perfect_data(controller.get_data())
            controller.override_dataframe(list(perfect_data.values()), is_hard=True)
            controller.update_file(same_file=False)
            
            print(f"Обработан: {excel_file.name}")
            
        except Exception as e:
            print(f"Ошибка обработки {excel_file.name}: {e}")
```

## Типы данных

### DFType
```python
DFType = list[XLSGood]  # Список словарей с строковыми значениями
```

### XLSGood
```python
XLSGood = dict[str, str]  # Словарь строковых пар ключ-значение
```

### IdfyGoods
```python
IdfyGoods = dict[int, XLSGood]  # Словарь с числовыми ID в качестве ключей
```

## Исключения

### `ContentLengthError`
Вызывается при отсутствии данных в файле.

### `WrongSheetListError`
Вызывается при невозможности найти корректный лист с данными.

### `LocalIDError`
Вызывается при отсутствии обязательного поля `local_id`.

### `EmptyIdfyNotNullDictException`
Вызывается при пустых perfect-данных.

## Конфигурация

Класс зависит от конфигурационных констант, определенных в:

- `ColumnStrings` — названия колонок и полей
- `System` — системные константы и настройки

## Зависимости

- **pandas** — работа с Excel-файлами и DataFrame
- **openpyxl** — движок для работы с .xlsx файлами
- **deprecated** — пометка устаревших методов