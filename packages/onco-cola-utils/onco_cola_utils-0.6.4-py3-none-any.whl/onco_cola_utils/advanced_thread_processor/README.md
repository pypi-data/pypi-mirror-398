# AdvancedThreadProcessor

Продвинутый многопоточный процессор для параллельной обработки данных с расширенной статистикой, детальным логированием и колбэками завершения.

## Особенности

- **⚡ Умное распределение данных** — автоматическое разделение на оптимальные чанки
- **🔍 Детальное отслеживание** — информация о каждой попытке обработки с таймстампами
- **📊 Расширенная статистика** — успешные/неудачные операции, время выполнения, прогресс потоков
- **🔄 Гибкие повторы** — настраиваемые таймауты между попытками
- **🎯 Колбэки завершения** — автоматический вызов callback-функций с отчетом
- **📝 Продвинутое логирование** — детальный прогресс и диагностика ошибок

## Быстрый старт

### Базовая обработка

```python
from advanced_thread_processor import AdvancedThreadProcessor
import time

def process_item(item):
    """Простая функция обработки элемента"""
    time.sleep(0.01)
    return f"processed_{item}"

# Запуск обработки
data = [f"item_{i}" for i in range(1000)]
processor = AdvancedThreadProcessor(
    data_list=data,
    process_method=process_item,
    threads_count=4
)

results = processor.run()
print(f"Успешно обработано: {len(results)} элементов")
```

### Обработка с детальным отслеживанием

```python
def process_with_retries(item, thread_id: int):
    """Функция с доступом к ID потока"""
    # Имитация возможных ошибок
    if hash(item) % 10 == 0:  # 10% вероятность ошибки
        raise ValueError("Временная ошибка обработки")
    
    time.sleep(0.05)
    return {
        'original': item,
        'processed_by': thread_id,
        'result': item.upper()
    }

def completion_callback(report):
    """Callback при завершении обработки"""
    print(f"Обработка завершена!")
    print(f"Успешно: {report.stats.success}, Ошибки: {report.stats.failed}")
    print(f"Общее время: {report.stats.total_duration_str}")
    print(f"Процент успеха: {report.success_percentage}")

# Конфигурация с повторами и callback
processor = AdvancedThreadProcessor(
    data_list=["data_1", "data_2", "data_3", ...],  # 1000+ элементов
    process_method=process_with_retries,
    threads_count=5,
    max_attempts=3,                    # До 3 попыток при ошибках
    base_timeout=1.0,                  # Начальный таймаут 1 сек
    delta_timeout=0.5,                 # Увеличение таймаута на 0.5 сек за попытку
    pass_thread_id=True,               # Передавать ID потока в метод
    enable_detailed_logging=True,      # Детальное логирование
    on_complete_method=completion_callback  # Callback при завершении
)

results = processor.run()
```

## Детальная конфигурация

### Параметры инициализации

```python
processor = AdvancedThreadProcessor(
    data_list=data,                    # [ОБЯЗАТЕЛЬНО] Список данных для обработки
    process_method=processing_func,    # [ОБЯЗАТЕЛЬНО] Функция обработки элементов
    
    # Опциональные параметры:
    threads_count=5,                   # Количество потоков (по умолчанию: 5)
    max_attempts=1,                    # Макс. попыток при ошибках (по умолчанию: 1)
    base_timeout=5.0,                  # Базовый таймаут между попытками (по умолчанию: 5.0)
    delta_timeout=2.0,                 # Приращение таймаута за попытку (по умолчанию: 2.0)
    pass_thread_id=True,               # Передавать thread_id в метод (по умолчанию: True)
    enable_detailed_logging=True,      # Детальное логирование (по умолчанию: True)
    on_complete_method=callback_func   # Callback при завершении (по умолчанию: None)
)
```

### Требования к методам обработки

#### Простой метод
```python
def process_item(item):
    """
    item - один элемент из data_list
    Должен возвращать результат обработки
    Может выбрасывать исключения при ошибках
    """
    return processed_result
```

#### Метод с доступом к потоку
```python
def process_item_with_thread(item, thread_id: int):
    """
    thread_id - идентификатор потока (0, 1, 2, ...)
    Полезно для логирования или специфичной логики потока
    """
    return {
        'item': item,
        'thread': thread_id,
        'result': perform_processing(item)
    }
```

#### Callback завершения
```python
def completion_callback(report: CompletionReport):
    """
    Вызывается при завершении всей обработки
    report содержит полную статистику и результаты
    """
    print(f"Обработка завершена: {report.stats.success}/{report.stats.total}")
    print(f"Время выполнения: {report.stats.total_duration_str}")
```

## Расширенные сценарии

### Обработка с анализом ошибок

```python
# Запуск обработки
processor = AdvancedThreadProcessor(
    data_list=large_dataset,
    process_method=complex_processing,
    threads_count=8,
    max_attempts=2,
    enable_detailed_logging=True
)

results = processor.run()

# Анализ результатов
stats = processor.statistics
failed_report = processor.get_failed_items_report()

print(f"Общая статистика:")
print(f"  Успешно: {stats.success}")
print(f"  Ошибки: {stats.failed}")
print(f"  Всего: {stats.total}")

print(f"\nДетали по ошибкам:")
for fail in failed_report:
    print(f"  Элемент: {fail['item']}")
    print(f"    Ошибка: {fail['error_message']}")
    print(f"    Попыток: {fail['attempts_made']}")
```

### Пакетная обработка файлов

```python
from pathlib import Path

def process_file(file_path, thread_id: int):
    """Обработка одного файла с логированием"""
    print(f"Поток {thread_id}: Обрабатываю {file_path.name}")
    
    try:
        # Чтение и обработка файла
        content = file_path.read_text()
        processed_content = content.upper()
        
        # Сохранение результата
        output_path = Path('processed') / file_path.name
        output_path.write_text(processed_content)
        
        return {
            'file': file_path.name,
            'status': 'success',
            'size': len(content)
        }
    except Exception as e:
        raise Exception(f"Ошибка обработки {file_path.name}: {e}")

# Сбор и обработка файлов
files = list(Path('data/').glob('*.txt'))
processor = AdvancedThreadProcessor(
    data_list=files,
    process_method=process_file,
    threads_count=3,
    pass_thread_id=True,
    max_attempts=2
)

results = processor.run()
```

### Мониторинг прогресса в реальном времени

```python
def progress_callback(report):
    """Callback для мониторинга прогресса"""
    stats = report.stats
    progress = (stats.success + stats.failed) / stats.total * 100
    
    print(f"Прогресс: {progress:.1f}%")
    print(f"  Успешно: {stats.success}")
    print(f"  Ошибки: {stats.failed}")
    print(f"  Активные потоки: {len(stats.thread_timings)}")
    
    # Логирование времени выполнения потоков
    for thread_id, timing in stats.thread_timings.items():
        if timing.duration_str:
            print(f"  Поток {thread_id}: {timing.duration_str}")

processor = AdvancedThreadProcessor(
    data_list=large_dataset,
    process_method=processing_function,
    threads_count=6,
    on_complete_method=progress_callback
)
```

## Анализ результатов

### Доступ к статистике

```python
stats = processor.statistics

# Основные метрики
print(f"Успешно: {stats.success}")
print(f"Ошибки: {stats.failed}") 
print(f"Всего: {stats.total}")

# Временные метрики
print(f"Начало: {stats.total_start_time_str}")
print(f"Окончание: {stats.total_end_time_str}")
print(f"Длительность: {stats.total_duration_str}")

# Статистика потоков
for thread_id, timing in stats.thread_timings.items():
    print(f"Поток {thread_id}: {timing.duration_str}")

# Детальные результаты
for item_key, result in stats.detailed_results.items():
    if not result.success:
        print(f"Ошибка обработки {result.item}: {result.error_message}")
```

### Отчет по ошибкам

```python
failed_items = processor.get_failed_items_report()

for fail in failed_items:
    print(f"Элемент: {fail['item']}")
    print(f"  Поток: {fail['thread_id']}")
    print(f"  Ошибка: {fail['error_message']}")
    print(f"  Сделано попыток: {fail['attempts_made']}")
    print(f"  Время последней попытки: {fail['last_attempt_time']}")
```

## Модели данных

### CompletionReport
```python
{
    "stats": ProcessorStats,
    "results": List[Any], 
    "thread_data_dict": Dict[int, List[Any]],
    "processing_time": float,
    "success_rate": float,
    "success_percentage": "95.5%"
}
```

### ProcessorStats
```python
{
    "success": 955,
    "failed": 45, 
    "total": 1000,
    "threads_used": 5,
    "chunk_sizes": {0: 200, 1: 200, 2: 200, 3: 200, 4: 200},
    "thread_timings": {
        0: ThreadTiming(duration_str="45.2 сек"),
        1: ThreadTiming(duration_str="43.8 сек"),
        ...
    },
    "total_duration_str": "46.1 сек",
    "detailed_results": {
        "item_1": ItemProcessingResult(success=True, ...),
        "item_2": ItemProcessingResult(success=False, ...)
    },
    "exhausted_attempts_items": ["item_25", "item_67"]
}
```

### ItemProcessingResult
```python
{
    "item": "original_data",
    "success": False,
    "error_message": "Timeout exceeded", 
    "attempts": [
        AttemptInfo(attempt_number=1, success=False, error_message="Network error"),
        AttemptInfo(attempt_number=2, success=False, error_message="Timeout exceeded")
    ],
    "total_attempts": 3,
    "thread_id": 2
}
```

## Особенности логирования

Процессор предоставляет детальное логирование:

```
2024-01-15 10:30:15 - [TH=2] Попытка 1/3: ОШИБКА - item_123 | Ошибка: Network error | Следующая попытка через: 1.0 сек.
2024-01-15 10:30:16 - [TH=2] Попытка 2/3: УСПЕШНО - item_123
2024-01-15 10:30:20 - Поток 3: обработано 100/250 элементов
2024-01-15 10:30:25 - Поток 1 завершил работу. Обработано: 245/250 элементов
```

## Производительность

- **Автоматическая балансировка** — данные равномерно распределяются между потоками
- **Минимальные блокировки** — только для обновления статистики
- **Эффективное использование памяти** — данные не копируются без необходимости  
- **Прогрессивные таймауты** — умные задержки между повторными попытками
- **Масштабируемость** — от десятков до сотен тысяч элементов

## Обработка ошибок

- **Автоматические повторы** — настраиваемое количество попыток с экспоненциальными таймаутами
- **Изоляция потоков** — ошибки в одном потоке не влияют на другие
- **Детальная диагностика** — полная информация о каждой неудачной попытке
- **Гибкое восстановление** — возможность продолжить обработку после ошибок