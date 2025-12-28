"""
ベンチマークレポーターのテスト
"""

from docgen.benchmark import BenchmarkRecorder, BenchmarkReporter
from docgen.benchmark.models import BenchmarkResult


class TestBenchmarkReporter:
    """BenchmarkReporterのテスト"""

    def test_generate_markdown(self):
        """Markdownレポート生成のテスト"""
        recorder = BenchmarkRecorder()
        recorder.clear()

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

        reporter = BenchmarkReporter(recorder)
        markdown = reporter.generate_markdown()

        assert "ベンチマーク結果" in markdown
        assert "test1" in markdown
        assert "test2" in markdown
        assert "1.00s" in markdown or "1000.00ms" in markdown

    def test_generate_json(self):
        """JSONレポート生成のテスト"""
        recorder = BenchmarkRecorder()
        recorder.clear()

        result = BenchmarkResult(
            name="test",
            duration=1.0,
            memory_peak=1000,
            memory_delta=500,
        )

        recorder.record(result)

        reporter = BenchmarkReporter(recorder)
        json_data = reporter.generate_json()

        assert "total_duration" in json_data
        assert "results" in json_data
        assert len(json_data["results"]) == 1

    def test_detect_bottlenecks(self):
        """ボトルネック検出のテスト"""
        recorder = BenchmarkRecorder()
        recorder.clear()

        # ボトルネックとなる処理（全体の10%以上）
        result1 = BenchmarkResult(
            name="bottleneck",
            duration=5.0,
            memory_peak=1000,
            memory_delta=500,
        )
        # 通常の処理（全体の10%未満）
        result2 = BenchmarkResult(
            name="normal",
            duration=0.5,  # 全体の約8.3%（10%未満）
            memory_peak=1000,
            memory_delta=500,
        )

        recorder.record(result1)
        recorder.record(result2)

        reporter = BenchmarkReporter(recorder)
        bottlenecks = reporter.detect_bottlenecks(threshold_percent=10.0)

        assert "bottleneck" in bottlenecks
        assert "normal" not in bottlenecks
