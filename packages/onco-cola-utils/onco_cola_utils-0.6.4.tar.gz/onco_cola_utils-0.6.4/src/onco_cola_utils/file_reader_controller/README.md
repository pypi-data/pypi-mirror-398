# FileReaderController

Простой и надежный контроллер для безопасной работы с текстовыми файлами. Обеспечивает атомарные операции чтения и записи с обработкой ошибок и автоматическим созданием директорий.

## Особенности

- **🛡️ Безопасные операции** — полная обработка исключений с трассировкой
- **📁 Автоматическое создание директорий** — не требует предварительной подготовки путей
- **🔧 Единая кодировка** — гарантированное использование UTF-8 для всех операций
- **⚡ Простой API** — только два статических метода для всех операций
- **📝 Детальное логирование** — полная трассировка ошибок при сбоях

## Установка

```python
# Код полностью самодостаточен, не требует внешних зависимостей
# Просто скопируйте класс в ваш проект

from pathlib import Path
from file_reader_controller import FileReaderController
```

## Быстрый старт

### Запись текста в файл

```python
from pathlib import Path
from file_reader_controller import FileReaderController

# Создание файла с автоматическим созданием директорий
file_path = Path("data/output/report.txt")
content = "Это содержимое файла\nС новой строкой"

success = FileReaderController.save_text(file_path, content)
if success:
    print("Файл успешно сохранён")
else:
    print("Ошибка сохранения файла")
```

### Чтение текста из файла

```python
from pathlib import Path
from file_reader_controller import FileReaderController

# Чтение файла
file_path = Path("data/config.txt")
content = FileReaderController.read_text(file_path)

if content is not False:
    print(f"Содержимое файла:\n{content}")
else:
    print("Файл не удалось прочитать")
```

### Комплексный пример

```python
from pathlib import Path
from file_reader_controller import FileReaderController

def process_data_file(input_path: Path, output_path: Path) -> bool:
    """
    Обрабатывает файл: читает, преобразует и сохраняет результат
    """
    # Чтение исходного файла
    input_content = FileReaderController.read_text(input_path)
    if input_content is False:
        print("Ошибка чтения исходного файла")
        return False
    
    # Преобразование содержимого (пример)
    processed_content = input_content.upper() + "\n# Обработано FileReaderController"
    
    # Сохранение результата
    success = FileReaderController.save_text(output_path, processed_content)
    if not success:
        print("Ошибка сохранения обработанного файла")
        return False
    
    print("Файл успешно обработан")
    return True

# Использование
input_file = Path("input/data.txt")
output_file = Path("output/processed_data.txt")
process_data_file(input_file, output_file)
```

## API Reference

### Статические методы

#### `FileReaderController.save_text(file_path: Path, content: str) -> bool`

Безопасно записывает текст в файл с созданием необходимых директорий.

**Параметры:**
- `file_path` — путь к файлу для записи (объект Path)
- `content` — строковое содержимое для записи

**Возвращает:**
- `True` — если запись успешно выполнена
- `False` — если произошла ошибка записи

**Особенности:**
- Автоматически создает все родительские директории
- Использует кодировку UTF-8
- Выводит полную трассировку ошибок в консоль при сбое

```python
# Пример использования
file_path = Path("deep/nested/directory/file.txt")
content = "Любой текст для сохранения"

if FileReaderController.save_text(file_path, content):
    print("Успех!")
else:
    print("Ошибка!")
```

#### `FileReaderController.read_text(file_path: Path) -> Union[str, bool]`

Безопасно читает содержимое текстового файла.

**Параметры:**
- `file_path` — путь к файлу для чтения (объект Path)

**Возвращает:**
- `str` — содержимое файла в случае успеха
- `False` — если произошла ошибка чтения

**Особенности:**
- Использует кодировку UTF-8
- Выводит полную трассировку ошибок в консоль при сбое
- Возвращает False вместо выброса исключения

```python
# Пример использования
file_path = Path("config/settings.txt")
content = FileReaderController.read_text(file_path)

if content is not False:
    print(f"Файл прочитан: {len(content)} символов")
    # Работа с содержимым
    lines = content.split('\n')
else:
    print("Не удалось прочитать файл")
```

## Примеры использования

### Создание лог-файлов

```python
from datetime import datetime
from pathlib import Path
from file_reader_controller import FileReaderController

def log_message(log_dir: Path, message: str) -> bool:
    """Записывает сообщение в лог-файл с timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = log_dir / "application.log"
    
    # Читаем существующее содержимое
    existing_content = FileReaderController.read_text(log_file)
    if existing_content is False:
        existing_content = ""
    
    # Добавляем новую запись
    new_content = existing_content + f"[{timestamp}] {message}\n"
    
    # Сохраняем обновлённый лог
    return FileReaderController.save_text(log_file, new_content)

# Использование
log_dir = Path("logs/2024")
log_message(log_dir, "Приложение запущено")
log_message(log_dir, "Выполнена обработка данных")
```

### Работа с конфигурационными файлами

```python
import json
from pathlib import Path
from file_reader_controller import FileReaderController

def load_config(config_path: Path) -> dict:
    """Загружает JSON конфигурацию из файла"""
    content = FileReaderController.read_text(config_path)
    if content is False:
        return {}  # Возвращаем пустой конфиг при ошибке
    
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        print("Ошибка парсинга JSON конфигурации")
        return {}

def save_config(config_path: Path, config: dict) -> bool:
    """Сохраняет JSON конфигурацию в файл"""
    try:
        content = json.dumps(config, indent=2, ensure_ascii=False)
        return FileReaderController.save_text(config_path, content)
    except Exception as e:
        print(f"Ошибка сериализации конфигурации: {e}")
        return False

# Использование
config_file = Path("config/app_settings.json")

# Загрузка конфигурации
config = load_config(config_file)
if not config:
    # Создание конфигурации по умолчанию
    config = {"debug": True, "max_workers": 4}

# Изменение и сохранение
config["debug"] = False
save_config(config_file, config)
```

### Пакетная обработка файлов

```python
from pathlib import Path
from file_reader_controller import FileReaderController

def process_text_files(source_dir: Path, target_dir: Path) -> None:
    """Обрабатывает все текстовые файлы в директории"""
    
    for text_file in source_dir.glob("*.txt"):
        try:
            # Чтение исходного файла
            content = FileReaderController.read_text(text_file)
            if content is False:
                print(f"Ошибка чтения: {text_file}")
                continue
            
            # Преобразование содержимого
            processed_content = content.upper()
            
            # Сохранение результата
            output_file = target_dir / f"processed_{text_file.name}"
            success = FileReaderController.save_text(output_file, processed_content)
            
            if success:
                print(f"Обработан: {text_file.name}")
            else:
                print(f"Ошибка сохранения: {text_file.name}")
                
        except Exception as e:
            print(f"Неожиданная ошибка при обработке {text_file.name}: {e}")

# Использование
source = Path("source_documents")
target = Path("processed_documents")
process_text_files(source, target)
```

## Обработка ошибок

Класс предоставляет детальную информацию об ошибках:

- **Автоматический вывод трассировки** — полный stack trace при исключениях
- **Четкие возвращаемые значения** — булевы флаги вместо исключений
- **Консольное логирование** — все ошибки выводятся в stdout

```python
# Пример обработки различных сценариев
file_path = Path("/readonly/system/file.txt")

result = FileReaderController.save_text(file_path, "test")
if not result:
    # В консоли будет выведена полная трассировка ошибки PermissionError
    print("Не удалось записать файл (см. детали выше)")
```

## Особенности реализации

### Кодировка
Все операции используют UTF-8 кодировку, что гарантирует корректную работу с Unicode символами.

### Создание директорий
Метод `save_text()` автоматически создает все необходимые родительские директории с помощью `Path.mkdir(parents=True, exist_ok=True)`.

### Безопасность операций
Оба метода защищены блоками try-except, что предотвращает аварийное завершение программы при ошибках ввода-вывода.