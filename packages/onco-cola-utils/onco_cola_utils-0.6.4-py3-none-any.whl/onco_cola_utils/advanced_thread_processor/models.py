from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AttemptInfo(BaseModel):
    """Информация о попытке обработки"""
    attempt_number: int
    success: bool
    error_message: Optional[str] = None
    timeout_before_next: Optional[float] = None
    timestamp: datetime


class ItemProcessingResult(BaseModel):
    """Результат обработки одного элемента"""
    item: Any
    success: bool = False  # Добавляем значение по умолчанию
    result: Optional[Any] = None
    error_message: Optional[str] = None
    attempts: List[AttemptInfo] = Field(default_factory=list)
    total_attempts: int = 0
    thread_id: Optional[int] = None


class ThreadTiming(BaseModel):
    """Модель временных меток потока"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    start_time_str: Optional[str] = None
    end_time_str: Optional[str] = None
    duration_str: Optional[str] = None


class ProcessorStats(BaseModel):
    """Модель статистики процессора"""
    success: int = 0
    failed: int = 0
    total: int = 0
    threads_used: int = 0
    chunk_sizes: Dict[int, int] = Field(default_factory=dict)
    thread_timings: Dict[int, ThreadTiming] = Field(default_factory=dict)
    total_start_time: Optional[datetime] = None
    total_end_time: Optional[datetime] = None
    total_duration: Optional[float] = None
    total_start_time_str: Optional[str] = None
    total_end_time_str: Optional[str] = None
    total_duration_str: Optional[str] = None
    pass_thread_id: bool = True
    supports_thread_id: bool = False
    detailed_results: Dict[str, ItemProcessingResult] = Field(default_factory=dict)
    exhausted_attempts_items: List[Any] = Field(default_factory=list)


class CompletionReport(BaseModel):
    """Отчет о завершении обработки"""
    stats: ProcessorStats
    results: List[Any]
    thread_data_dict: Dict[int, List[Any]]
    processing_time: float
    success_rate: float

    @property
    def success_percentage(self) -> str:
        """Процент успешных обработок"""
        if self.stats.total == 0:
            return "0%"
        return f"{(self.stats.success / self.stats.total) * 100:.1f}%"
