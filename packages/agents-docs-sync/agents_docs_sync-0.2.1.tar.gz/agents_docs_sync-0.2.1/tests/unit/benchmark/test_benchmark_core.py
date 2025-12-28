"""
ベンチマークコア機能のテスト
"""

import time

from docgen.benchmark import BenchmarkContext, BenchmarkRecorder, benchmark


class TestBenchmarkContext:
    """BenchmarkContextのテスト"""

    def test_benchmark_context_basic(self):
        """基本的なベンチマークコンテキストのテスト"""
        recorder = BenchmarkRecorder()
        recorder.clear()

        with BenchmarkContext("test_operation", recorder=recorder, enabled=True):
            time.sleep(0.01)  # 10ms待機

        results = recorder.get_results()
        assert len(results) == 1
        assert results[0].name == "test_operation"
        assert results[0].duration > 0

    def test_benchmark_context_disabled(self):
        """無効化されたベンチマークコンテキストのテスト"""
        recorder = BenchmarkRecorder()
        recorder.clear()

        with BenchmarkContext("test_operation", recorder=recorder, enabled=False):
            time.sleep(0.01)

        results = recorder.get_results()
        assert len(results) == 0

    def test_benchmark_decorator(self):
        """ベンチマークデコレータのテスト"""

        @benchmark("decorated_function", enabled=True)
        def test_function():
            time.sleep(0.01)
            return "result"

        recorder = BenchmarkRecorder.get_global()
        recorder.clear()

        result = test_function()
        assert result == "result"

        results = recorder.get_results()
        assert len(results) == 1
        assert results[0].name == "decorated_function"


class TestBenchmarkRecorder:
    """BenchmarkRecorderのテスト"""

    def test_recorder_record(self):
        """レコーダーの記録機能のテスト"""
        recorder = BenchmarkRecorder()
        recorder.clear()

        from docgen.benchmark.models import BenchmarkResult

        result1 = BenchmarkResult(
            name="test1",
            duration=1.0,
            memory_peak=1000,
            memory_delta=500,
        )
        result2 = BenchmarkResult(
            name="test2",
            duration=2.0,
            memory_peak=2000,
            memory_delta=1000,
        )

        recorder.record(result1)
        recorder.record(result2)

        results = recorder.get_results()
        assert len(results) == 2

    def test_recorder_summary(self):
        """レコーダーの集計機能のテスト"""
        recorder = BenchmarkRecorder()
        recorder.clear()

        from docgen.benchmark.models import BenchmarkResult

        result1 = BenchmarkResult(
            name="test1",
            duration=1.0,
            memory_peak=1000,
            memory_delta=500,
            cpu_percent=10.0,
        )
        result2 = BenchmarkResult(
            name="test2",
            duration=2.0,
            memory_peak=2000,
            memory_delta=1000,
            cpu_percent=20.0,
        )

        recorder.record(result1)
        recorder.record(result2)

        summary = recorder.get_summary()
        assert summary.total_duration == 3.0
        assert summary.total_results == 2
        assert summary.memory_peak_total == 2000
        assert summary.cpu_avg == 15.0

    def test_recorder_global(self):
        """グローバルレコーダーのテスト"""
        recorder1 = BenchmarkRecorder.get_global()
        recorder2 = BenchmarkRecorder.get_global()

        assert recorder1 is recorder2

        BenchmarkRecorder.reset_global()
        recorder3 = BenchmarkRecorder.get_global()

        assert recorder3 is not recorder1
