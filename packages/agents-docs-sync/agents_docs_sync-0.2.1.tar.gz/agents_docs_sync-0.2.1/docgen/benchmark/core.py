"""
ベンチマークコア機能

デコレータとコンテキストマネージャーを提供します。
"""

from collections.abc import Callable, Generator
from contextlib import contextmanager
import functools
import time
from typing import Any

import psutil

from .models import BenchmarkResult
from .recorder import BenchmarkRecorder
from .utils import get_current_process


class BenchmarkContext:
    """ベンチマーク測定用のコンテキストマネージャー"""

    def __init__(self, name: str, recorder: BenchmarkRecorder | None = None, enabled: bool = True):
        """
        初期化

        Args:
            name: 測定対象の処理名
            recorder: ベンチマークレコーダー（Noneの場合はグローバルレコーダーを使用）
            enabled: 測定を有効にするかどうか
        """
        self.name = name
        self.recorder = recorder or BenchmarkRecorder.get_global()
        self.enabled = enabled
        self.result: BenchmarkResult | None = None
        self._start_time: float | None = None
        self._start_memory: int | None = None
        self._process: psutil.Process | None = None

    def __enter__(self) -> "BenchmarkContext":
        """測定開始"""
        if not self.enabled:
            return self

        self._start_time = time.perf_counter()
        self._process = get_current_process()
        self._start_memory = self._process.memory_info().rss

        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """測定終了と結果記録"""
        if not self.enabled or self._start_time is None:
            return

        end_time = time.perf_counter()
        duration = end_time - self._start_time

        if self._process is None:
            self._process = get_current_process()

        end_memory = self._process.memory_info().rss
        memory_delta = end_memory - (self._start_memory or 0)
        memory_peak = end_memory

        # CPU使用率の計算（期間中の平均）
        try:
            cpu_percent = self._process.cpu_percent(interval=0.1)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            cpu_percent = 0.0

        self.result = BenchmarkResult(
            name=self.name,
            duration=duration,
            memory_peak=memory_peak,
            memory_delta=memory_delta,
            cpu_percent=cpu_percent,
        )

        if self.recorder:
            self.recorder.record(self.result)


def benchmark(name: str | None = None, enabled: bool = True) -> Callable:
    """
    関数の実行時間を測定するデコレータ

    Args:
        name: 測定対象の処理名（Noneの場合は関数名を使用）
        enabled: 測定を有効にするかどうか

    Returns:
        デコレータ関数

    Example:
        @benchmark("my_function")
        def my_function():
            # 処理
            pass
    """

    def decorator(func: Callable) -> Callable:
        benchmark_name = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with BenchmarkContext(benchmark_name, enabled=enabled):
                return func(*args, **kwargs)

        return wrapper

    return decorator


@contextmanager
def benchmark_context(
    name: str, recorder: BenchmarkRecorder | None = None, enabled: bool = True
) -> Generator[BenchmarkContext, None, None]:
    """
    ベンチマークコンテキストマネージャー（関数形式）

    Args:
        name: 測定対象の処理名
        recorder: ベンチマークレコーダー
        enabled: 測定を有効にするかどうか

    Yields:
        BenchmarkContextインスタンス

    Example:
        with benchmark_context("my_operation"):
            # 処理
            pass
    """
    with BenchmarkContext(name, recorder=recorder, enabled=enabled) as ctx:
        yield ctx
