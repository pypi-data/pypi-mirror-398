import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from threading import Lock
from typing import Any, Callable, Dict, List, Optional

from src.onco_cola_utils import log
from src.onco_cola_utils.advanced_thread_processor.constants import DefaultValues, ErrorMessages
from src.onco_cola_utils.advanced_thread_processor.models import (
    AttemptInfo, CompletionReport,
    ItemProcessingResult,
    ProcessorStats, ThreadTiming
)
from src.onco_cola_utils.advanced_thread_processor.utils import (
    MethodInspector,
    ProcessorLogger,
    TimeFormatter
)


print = log


class AdvancedThreadProcessor:
    def __init__(
        self,
        data_list: List[Any],
        process_method: Callable,
        threads_count: int = DefaultValues.THREADS_COUNT,
        max_attempts: int = DefaultValues.MAX_ATTEMPTS,
        base_timeout: float = DefaultValues.BASE_TIMEOUT,
        delta_timeout: float = DefaultValues.DELTA_TIMEOUT,
        pass_thread_id: bool = DefaultValues.PASS_THREAD_ID,
        enable_detailed_logging: bool = DefaultValues.ENABLE_DETAILED_LOGGING,
        on_complete_method: Optional[Callable] = DefaultValues.ON_COMPLETE_METHOD
    ):
        if not data_list:
            raise ValueError(ErrorMessages.EMPTY_DATA_LIST)

        self.data_list = data_list
        self.process_method = process_method
        self.threads_count = threads_count
        self.max_attempts = max_attempts
        self.base_timeout = base_timeout
        self.delta_timeout = delta_timeout
        self.pass_thread_id = pass_thread_id
        self.enable_detailed_logging = enable_detailed_logging
        self.on_complete_method = on_complete_method

        # Проверяем возможность передачи thread_id
        self._supports_thread_id = MethodInspector.supports_thread_id(process_method)

        if pass_thread_id and not self._supports_thread_id:
            raise ValueError(
                ErrorMessages.THREAD_ID_NOT_SUPPORTED.format(
                    method_name=process_method.__name__
                )
            )

        # Проверяем колбэк завершения если он указан
        if on_complete_method and not MethodInspector.supports_completion_report(
            on_complete_method
        ):
            raise ValueError(
                ErrorMessages.ON_COMPLETE_METHOD_INVALID
            )

        self.results = []
        self.stats = ProcessorStats(
            total=len(data_list),
            threads_used=threads_count,
            pass_thread_id=pass_thread_id,
            supports_thread_id=self._supports_thread_id
        )
        self._lock = Lock()
        self._thread_data_dict: Dict[int, List[Any]] = {}
        self._is_valid_threads = False

        print(f"Инициализация процессора: {len(data_list)} элементов, {threads_count} потоков")
        self._divide_by_threads()

    def _divide_by_threads(self) -> Dict[int, List[Any]]:
        """Делит данные на примерно равные части для каждого потока"""
        total_items = len(self.data_list)
        if total_items == 0:
            self._is_valid_threads = True
            return {}

        actual_threads = min(self.threads_count, total_items)
        base_chunk_size = total_items // actual_threads
        chunks_with_extra = total_items % actual_threads

        self._thread_data_dict = {}
        start_index = 0

        for thread_id in range(actual_threads):
            chunk_size = base_chunk_size + (1 if thread_id < chunks_with_extra else 0)
            end_index = start_index + chunk_size
            self._thread_data_dict[thread_id] = self.data_list[start_index:end_index]

            # Обновляем статистику через модель
            self.stats.chunk_sizes[thread_id] = chunk_size
            start_index = end_index

        self.stats.threads_used = actual_threads
        self._is_valid_threads = True

        print(f"Данные распределены по {actual_threads} потокам:")
        for thread_id, chunk in self._thread_data_dict.items():
            print(f"  Поток {thread_id}: {len(chunk)} элементов")

        return self._thread_data_dict

    def _process_with_retry(self, item, thread_id: int = None):
        """Обрабатывает один элемент с повторными попытками и детальным логированием"""
        item_key = str(item)
        processing_result = ItemProcessingResult(
            item=item,
            thread_id=thread_id,
            total_attempts=self.max_attempts
        )

        for attempt in range(self.max_attempts):
            try:
                if self.pass_thread_id and self._supports_thread_id and thread_id is not None:
                    result = self.process_method(item, thread_id=thread_id)
                else:
                    result = self.process_method(item)

                # Успешная попытка
                processing_result.success = True
                processing_result.result = result
                processing_result.attempts.append(
                    AttemptInfo(
                        attempt_number=attempt + 1,
                        success=True,
                        timestamp=datetime.now()
                    )
                )

                if self.enable_detailed_logging:
                    ProcessorLogger.log_attempt(
                        thread_id=thread_id or 0,
                        item=item,
                        attempt=attempt + 1,
                        max_attempts=self.max_attempts,
                        success=True
                    )

                with self._lock:
                    self.stats.success += 1
                    self.stats.detailed_results[item_key] = processing_result

                return result

            except Exception as e:
                error_msg = str(e)
                timeout = self.base_timeout + (attempt * self.delta_timeout)

                # Записываем информацию о неудачной попытке
                processing_result.attempts.append(
                    AttemptInfo(
                        attempt_number=attempt + 1,
                        success=False,
                        error_message=error_msg,
                        timeout_before_next=timeout if attempt < self.max_attempts - 1 else None,
                        timestamp=datetime.now()
                    )
                )

                if self.enable_detailed_logging:
                    ProcessorLogger.log_attempt(
                        thread_id=thread_id or 0,
                        item=item,
                        attempt=attempt + 1,
                        max_attempts=self.max_attempts,
                        success=False,
                        error_msg=error_msg,
                        timeout=timeout
                    )

                # Если это последняя попытка
                if attempt == self.max_attempts - 1:
                    processing_result.success = False
                    processing_result.error_message = error_msg

                    with self._lock:
                        self.stats.failed += 1
                        self.stats.detailed_results[item_key] = processing_result
                        self.stats.exhausted_attempts_items.append(item)

                    raise e

                # Ждем перед следующей попыткой
                time.sleep(timeout)

    def _process_thread_chunk(self, thread_id: int):
        """Обрабатывает чанк данных для одного потока"""
        print(f"Запуск потока {thread_id} с {len(self._thread_data_dict[thread_id])} элементами")

        thread_start_time = datetime.now()

        # Инициализируем timing для потока
        with self._lock:
            self.stats.thread_timings[thread_id] = ThreadTiming(
                start_time=thread_start_time
            )

        thread_data = self._thread_data_dict.get(thread_id, [])
        thread_results = []

        for i, item in enumerate(thread_data):
            if i % 100 == 0:  # Логируем прогресс каждые 100 элементов
                print(f"Поток {thread_id}: обработано {i}/{len(thread_data)} элементов")

            try:
                result = self._process_with_retry(item, thread_id)
                thread_results.append(result)
            except Exception as e:
                # Ошибка уже обработана в _process_with_retry
                print(
                    f"Поток {thread_id}: элемент {item} завершился с ошибкой после всех попыток: {e}"
                )
                pass

        print(
            f"Поток {thread_id} завершил работу. Обработано: {len(thread_results)}/{len(thread_data)}"
        )

        thread_end_time = datetime.now()
        thread_duration = (thread_end_time - thread_start_time).total_seconds()

        # Обновляем timing с форматированными строками
        with self._lock:
            self.stats.thread_timings[thread_id] = ThreadTiming(
                start_time=thread_start_time,
                end_time=thread_end_time,
                duration=thread_duration,
                start_time_str=TimeFormatter.format_datetime(thread_start_time),
                end_time_str=TimeFormatter.format_datetime(thread_end_time),
                duration_str=TimeFormatter.format_duration(thread_duration)
            )

        return thread_results

    def _call_completion_callback(self, processing_time: float):
        """Вызывает колбэк завершения если он указан"""
        if not self.on_complete_method:
            return

        try:
            # Создаем отчет о завершении
            success_rate = self.stats.success / self.stats.total if self.stats.total > 0 else 0
            report = CompletionReport(
                stats=self.statistics,
                results=self.results.copy(),
                thread_data_dict=self.thread_data_dict,
                processing_time=processing_time,
                success_rate=success_rate
            )

            # Вызываем колбэк
            self.on_complete_method(report=report)

        except Exception as e:
            print(f"Ошибка при вызове колбэка завершения: {e}")

    def run(self):
        """Запускает многопоточную обработку"""
        if not self._is_valid_threads:
            raise ValueError(ErrorMessages.DATA_NOT_PREPARED)

        if not self._thread_data_dict:
            print("Нет данных для обработки")
            return self.results

        print(f"Запуск обработки {len(self.data_list)} элементов в {self.threads_count} потоках")
        self.stats.total_start_time = datetime.now()

        try:
            with ThreadPoolExecutor(max_workers=self.threads_count) as executor:
                future_to_thread = {
                    executor.submit(self._process_thread_chunk, thread_id): thread_id
                    for thread_id in self._thread_data_dict.keys()
                }

                for future in as_completed(future_to_thread):
                    try:
                        thread_results = future.result()
                        self.results.extend(thread_results)
                        print(
                            f"Поток {future_to_thread[future]} завершился успешно. Результатов: {len(thread_results)}"
                        )
                    except Exception as e:
                        print(f"Критическая ошибка в потоке {future_to_thread[future]}: {e}")

        except Exception as e:
            print(f"Ошибка при выполнении потоков: {e}")
            raise

        self.stats.total_end_time = datetime.now()
        total_duration = (self.stats.total_end_time - self.stats.total_start_time).total_seconds()

        # Обновляем общую статистику с форматированными строками
        self.stats.total_duration = total_duration
        self.stats.total_start_time_str = TimeFormatter.format_datetime(self.stats.total_start_time)
        self.stats.total_end_time_str = TimeFormatter.format_datetime(self.stats.total_end_time)
        self.stats.total_duration_str = TimeFormatter.format_duration(total_duration)

        print(f"Обработка завершена. Всего результатов: {len(self.results)}")

        # Вызываем колбэк завершения
        self._call_completion_callback(total_duration)

        return self.results

    @property
    def thread_data_dict(self) -> Dict[int, List[Any]]:
        return self._thread_data_dict.copy()

    @property
    def statistics(self) -> ProcessorStats:
        """Возвращает статистику (копию для безопасности)"""
        return self.stats.model_copy()

    @property
    def is_ready(self) -> bool:
        return self._is_valid_threads and bool(self._thread_data_dict)

    def get_failed_items_report(self) -> List[Dict]:
        """Возвращает отчет по неудачно обработанным элементам"""
        report = []
        for item_key, result in self.stats.detailed_results.items():
            if not result.success:
                report.append(
                    {
                        'item': result.item,
                        'thread_id': result.thread_id,
                        'error_message': result.error_message,
                        'attempts_made': len(result.attempts),
                        'max_attempts': result.total_attempts,
                        'last_attempt_time': (
                            result.attempts[-1].timestamp if result.attempts else None
                        )
                    }
                )
        return report
