from typing import Callable, Optional


class TimeFormats:
    """Форматы времени"""
    DATETIME_DISPLAY = '%Y-%m-%d %H:%M:%S'
    DATE_ONLY = '%Y-%m-%d'
    TIME_ONLY = '%H:%M:%S'


class DefaultValues:
    """Значения по умолчанию"""
    THREADS_COUNT = 5
    MAX_ATTEMPTS = 1
    BASE_TIMEOUT = 5.0
    DELTA_TIMEOUT = 2.0
    PASS_THREAD_ID = True
    ENABLE_DETAILED_LOGGING = True
    ON_COMPLETE_METHOD: Optional[Callable] = None


class ErrorMessages:
    """Сообщения об ошибках"""
    DATA_NOT_PREPARED = "Данные для потоков не подготовлены"
    THREAD_ID_NOT_SUPPORTED = "Метод {method_name} не поддерживает параметр thread_id: int. Используйте pass_thread_id=False или добавьте параметр thread_id: int в метод."
    ON_COMPLETE_METHOD_INVALID = "Метод on_complete_method должен принимать параметр report: CompletionReport"
    EMPTY_DATA_LIST = "Список данных не может быть пустым"
