import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Union

try:
    import ijson

    IJSON_AVAILABLE = True
except ImportError:
    IJSON_AVAILABLE = False


class JsonReader:
    """
    Умный читатель и валидатор JSON-файлов.

    Предоставляет безопасный, быстрый и удобный интерфейс для:
     - Валидации синтаксиса JSON
     - Проверки целостности файла
     - Получения метаданных без полной загрузки
     - Ленивой загрузки содержимого
     - Хеширования и контроля изменений

    Поддерживает два режима:
     1. Обычный (`use_stream=False`) — подходит для файлов до ~50 МБ.
     2. Потоковый (`use_stream=True`) — для больших файлов (>50 МБ), требует `ijson`.

    Пример использования:
        reader = JsonReader("data.json")
        if reader.is_valid:
            print(reader.data)  # Данные загружаются только при первом доступе
    """

    def __init__(self, file_path: Union[str, Path], use_stream: bool = False):
        """
        Инициализация читателя JSON.

        Args:
            file_path: Путь к JSON-файлу.
            use_stream: Использовать потоковую валидацию (для больших файлов).
                        Требует установленного пакета `ijson`.

        Raises:
            ValueError: Если use_stream=True, но ijson не установлен.
            FileNotFoundError: Если файл не существует.
        """
        self._file_path: Path = Path(file_path).resolve()
        self._use_stream: bool = use_stream
        self._data: Optional[Any] = None
        self._validation_error: Optional[Exception] = None

        if use_stream and not IJSON_AVAILABLE:
            raise ValueError(
                "Потоковая валидация требует установки 'ijson'. "
                "Выполните: pip install ijson"
            )

        if not self._file_path.exists():
            raise FileNotFoundError(f"Файл не найден: {self._file_path}")

    @property
    def path(self) -> Path:
        """Полный путь к файлу."""
        return self._file_path

    @property
    def name(self) -> str:
        """Имя файла (без пути)."""
        return self._file_path.name

    @property
    def stem(self) -> str:
        """Имя файла без расширения."""
        return self._file_path.stem

    @property
    def suffix(self) -> str:
        """Расширение файла (включая точку)."""
        return self._file_path.suffix

    @property
    def exists(self) -> bool:
        """True, если файл существует."""
        return self._file_path.exists()

    @property
    def is_file(self) -> bool:
        """True, если путь указывает на файл (не директорию)."""
        return self._file_path.is_file()

    @property
    def size_bytes(self) -> int:
        """Размер файла в байтах."""
        return self._file_path.stat().st_size if self.exists else 0

    @property
    def size_mb(self) -> float:
        """Размер файла в мегабайтах (округлён до 2 знаков)."""
        return round(self.size_bytes / (1024 * 1024), 2)

    @property
    def created_at(self) -> Optional[datetime]:
        """Дата создания файла (точная семантика зависит от ОС)."""
        if not self.exists:
            return None
        timestamp = self._file_path.stat().st_ctime
        return datetime.fromtimestamp(timestamp)

    @property
    def modified_at(self) -> Optional[datetime]:
        """Дата последнего изменения файла."""
        if not self.exists:
            return None
        timestamp = self._file_path.stat().st_mtime
        return datetime.fromtimestamp(timestamp)

    @property
    def lines(self) -> int:
        """Примерное количество строк в файле (оценка)."""
        if not self.exists or not self.is_file:
            return 0
        try:
            with self._file_path.open('rb') as f:
                return sum(1 for _ in f)
        except Exception:
            return 0

    @property
    def sha256(self) -> str:
        """SHA-256 хеш содержимого файла."""
        if not self.exists:
            return ""
        hash_sha256 = hashlib.sha256()
        with self._file_path.open('rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    @property
    def data(self) -> Any:
        """
        Загружает и возвращает содержимое JSON-файла.

        Ленивая загрузка: данные читаются только при первом вызове.
        При повторных вызовах используется кеш.

        Returns:
            Словарь, список или примитив (в зависимости от JSON).

        Raises:
            ValueError: Если JSON некорректен или файл недоступен.
            OSError: Ошибка чтения файла.
        """
        if self._data is not None:
            return self._data

        if not self.is_valid:
            raise ValueError(f"Невозможно прочитать файл: {self._validation_error}")

        try:
            text = self._file_path.read_text(encoding='utf-8')
            self._data = json.loads(text)
            return self._data
        except json.JSONDecodeError as e:
            raise ValueError(f"Ошибка парсинга JSON: {e}")
        except UnicodeDecodeError as e:
            raise ValueError(f"Файл не в UTF-8: {e}")
        except Exception as e:
            raise OSError(f"Ошибка чтения файла: {e}")

    @property
    def data_type(self) -> Optional[str]:
        """Тип корневого объекта: 'dict', 'list', 'str' и т.д. None — если ошибка."""
        try:
            data = self.data
            return type(data).__name__
        except Exception:
            return None

    @property
    def length(self) -> Optional[int]:
        """Длина корневого объекта (len), если это list/dict/str. Иначе None."""
        try:
            data = self.data
            if isinstance(data, (list, dict, str)):
                return len(data)
            return None
        except Exception:
            return None

    @property
    def is_valid(self) -> bool:
        """
        Проверяет, является ли файл валидным JSON.

        При первом вызове выполняется полная валидация.
        Результат кешируется.

        Returns:
            True, если файл существует, читаем и содержит валидный JSON.
        """
        if self._validation_error is not None:
            return False
        if not self.exists:
            self._validation_error = FileNotFoundError(f"Файл не найден: {self._file_path}")
            return False
        if not self.is_file:
            self._validation_error = IsADirectoryError(f"Не файл: {self._file_path}")
            return False
        if self.suffix.lower() != '.json':
            self._validation_error = ValueError(f"Ожидался .json: {self._file_path}")
            return False

        try:
            if self._use_stream:
                if not IJSON_AVAILABLE:
                    raise ImportError("ijson не установлен")
                with self._file_path.open('rb') as f:
                    parser = ijson.parse(f)
                    for _ in parser:
                        pass
            else:
                text = self._file_path.read_text(encoding='utf-8')
                data = json.loads(text)
                if not isinstance(data, (dict, list)):
                    raise ValueError(
                        f"Корень должен быть dict/list, получен: {type(data).__name__}"
                    )
            return True
        except (json.JSONDecodeError, ValueError, ImportError, OSError) as e:
            self._validation_error = e
            return False
        except Exception as e:
            self._validation_error = OSError(f"Неожиданная ошибка: {e}")
            return False

    @property
    def validation_error(self) -> Optional[str]:
        """Сообщение об ошибке валидации или None, если всё в порядке."""
        return str(self._validation_error) if self._validation_error else None

    def validate_structure(self, required_keys: Optional[List[str]] = None) -> bool:
        """
        Проверяет структуру JSON: наличие обязательных ключей (если это dict).

        Args:
            required_keys: Список ключей, которые должны присутствовать в корне.

        Returns:
            True, если структура соответствует.

        Raises:
            ValueError: Если файл не валиден или не dict.
        """
        if not self.is_valid:
            raise ValueError(f"Файл не валиден: {self.validation_error}")

        data = self.data
        if not isinstance(data, dict):
            raise ValueError("Требуется JSON-объект (dict)")

        if required_keys:
            return all(key in data for key in required_keys)

        return True

    def iter_items(self, prefix: str = '') -> Generator[Any, None, None]:
        """
        Потоковое чтение элементов (для списков или объектов большого размера).
        Работает только в режиме `use_stream=True`.

        Yields:
            Элементы из массива или пары ключ-значение из объекта.

        Example:
            for item in reader.iter_items():
                print(item)
        """
        if not self._use_stream:
            raise RuntimeError("iter_items() требует use_stream=True")

        if not IJSON_AVAILABLE:
            raise RuntimeError("Требуется ijson для потокового чтения")

        with self._file_path.open('rb') as f:
            if isinstance(self.data, list):
                for item in ijson.items(f, 'item'):
                    yield item
            elif isinstance(self.data, dict):
                for key, value in ijson.kvitems(f, ''):
                    yield key, value
            else:
                yield self.data

    def __repr__(self) -> str:
        return f"<JsonReader valid={self.is_valid} path='{self.name}'>"

    def __bool__(self) -> bool:
        return self.is_valid

    def info(self) -> Dict[str, Any]:
        """
        Возвращает словарь с основными метаданными.

        Returns:
            {
                "path": str,
                "valid": bool,
                "error": str | None,
                "type": str | None,
                "length": int | None,
                "size_mb": float,
                "lines": int,
                "sha256": str,
                "created_at": str | None,
                "modified_at": str | None
            }
        """
        return {
            "path": str(self.path),
            "valid": self.is_valid,
            "error": self.validation_error,
            "type": self.data_type,
            "length": self.length,
            "size_mb": self.size_mb,
            "lines": self.lines,
            "sha256": self.sha256,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
        }

    @staticmethod
    def write(
        data: Any,
        file_path: str | Path,
        indent: Optional[int] = 2,
        ensure_ascii: bool = False,
        create_parents: bool = True,
        atomic: bool = True
    ) -> None:
        """
        Записывает данные в JSON-файл. Поддерживает Pydantic, Path, int-keys и др.
        """
        path = Path(file_path).resolve()

        if create_parents:
            path.parent.mkdir(parents=True, exist_ok=True)

        if atomic:
            temp_path = path.with_suffix(f"{path.suffix}.tmp")
            target_path = temp_path
        else:
            target_path = path

        try:
            # Преобразуем данные с помощью custom serializer
            serialized = JsonReader._serialize(data)

            with open(target_path, 'w', encoding='utf-8') as f:
                json.dump(
                    serialized,
                    f,
                    indent=indent,
                    ensure_ascii=ensure_ascii,
                    default=JsonReader._fallback_serializer
                )
                f.write('\n')

            if atomic and temp_path.exists():
                temp_path.replace(path)

        except Exception as e:
            raise OSError(f"Ошибка записи JSON-файла {path}: {e}")

    @staticmethod
    def _fallback_serializer(obj: Any) -> Any:
        """
        Резервный сериализатор для json.dump().
        Должен возвращать сериализуемый тип.
        """
        if isinstance(obj, Path):
            return str(obj.as_posix())
        elif hasattr(obj, 'model_dump'):
            return JsonReader._serialize(obj.model_dump())
        else:
            return repr(obj)

    @staticmethod
    def _serialize(data: Any) -> Any:
        """Рекурсивно сериализует структуру с поддержкой моделей, путей и int-ключей."""
        if hasattr(data, 'model_dump'):  # Pydantic v2
            return JsonReader._serialize(data.model_dump())
        elif isinstance(data, dict):
            return {
                str(k): JsonReader._serialize(v)  # Принудительно str(k)
                for k, v in data.items()
            }
        elif isinstance(data, (list, tuple)):
            return [JsonReader._serialize(item) for item in data]
        elif isinstance(data, Path):
            return str(data.as_posix())  # или просто str(data) — зависит от ОС
        elif isinstance(data, (int, float, str, bool)) or data is None:
            return data
        elif isinstance(data, set):
            return JsonReader._serialize(list(data))
        else:
            return repr(data)  # fallback

    @staticmethod
    def write_compact(data: Any, file_path: str | Path) -> None:
        """Быстрая компактная запись без отступов."""
        JsonReader.write(data, file_path, indent=None, ensure_ascii=False)

    @staticmethod
    def write_pretty(data: Any, file_path: str | Path) -> None:
        """Красивая форматированная запись."""
        JsonReader.write(data, file_path, indent=2, ensure_ascii=False)
