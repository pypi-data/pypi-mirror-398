import inspect
from datetime import datetime, timedelta
from typing import Any

from src.onco_cola_utils.advanced_thread_processor.models import CompletionReport
from src.onco_cola_utils.advanced_thread_processor.constants import TimeFormats


class TimeFormatter:
    """Утилиты для форматирования времени"""

    @staticmethod
    def format_duration(seconds: float) -> str:
        """Форматирует время в формате 'ДДД дн. ЧЧ ч. ММ мин. СС сек.'"""
        if seconds <= 0:
            return "0 сек."

        td = timedelta(seconds=seconds)
        days = td.days
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        parts = []
        if days > 0:
            parts.append(f"{days} дн.")
        if hours > 0:
            parts.append(f"{hours:02d} ч.")
        if minutes > 0:
            parts.append(f"{minutes:02d} мин.")
        if seconds > 0 or not parts:
            parts.append(f"{seconds:02d} сек.")

        return " ".join(parts)

    @staticmethod
    def format_datetime(dt) -> str:
        """Форматирует datetime в строку"""
        if not dt:
            return ""
        return dt.strftime(TimeFormats.DATETIME_DISPLAY)


class MethodInspector:
    """Утилиты для анализа методов"""

    @staticmethod
    def supports_thread_id(method) -> bool:
        """
        Проверяет, поддерживает ли метод параметр thread_id: int
        """
        import inspect

        try:
            sig = inspect.signature(method)

            if 'thread_id' in sig.parameters:
                param = sig.parameters['thread_id']
                # Проверяем аннотацию типа
                if param.annotation in (int, inspect.Parameter.empty):
                    return True
                # Если аннотация указана, проверяем что это int
                elif hasattr(param.annotation, '__origin__'):
                    return param.annotation.__origin__ is int
                else:
                    return param.annotation is int

            return False

        except (ValueError, TypeError):
            return False

    @staticmethod
    def supports_completion_report(method) -> bool:
        """
        Проверяет, поддерживает ли метод параметр report: CompletionReport
        """
        try:
            sig = inspect.signature(method)

            if 'report' in sig.parameters:
                param = sig.parameters['report']
                # Проверяем аннотацию типа
                if param.annotation in (CompletionReport, inspect.Parameter.empty):
                    return True
                # Если аннотация указана, проверяем что это CompletionReport
                elif hasattr(param.annotation, '__origin__'):
                    return param.annotation.__origin__ is CompletionReport
                else:
                    return param.annotation is CompletionReport

            return False

        except (ValueError, TypeError):
            return False


class ProcessorLogger:
    """Логгер для процессора"""

    @staticmethod
    def log_attempt(
        thread_id: int, item: Any, attempt: int, max_attempts: int,
        success: bool, error_msg: str = None, timeout: float = None
    ):
        """Логирует информацию о попытке"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        status = "УСПЕШНО" if success else "ОШИБКА"

        if success:
            print(
                f"{timestamp} - [TH={thread_id}] Попытка {attempt}/{max_attempts}: {status} - {item}"
            )
        else:
            if attempt < max_attempts:
                print(
                    f"{timestamp} - [TH={thread_id}] Попытка {attempt}/{max_attempts}: {status} - {item} | "
                    f"Ошибка: {error_msg} | Следующая попытка через: {timeout:.1f} сек."
                )
            else:
                print(
                    f"{timestamp} - [TH={thread_id}] Попытка {attempt}/{max_attempts}: {status} - {item} | "
                    f"Ошибка: {error_msg} | ВСЕ ПОПЫТКИ ИСЧЕРПАНЫ!"
                )
