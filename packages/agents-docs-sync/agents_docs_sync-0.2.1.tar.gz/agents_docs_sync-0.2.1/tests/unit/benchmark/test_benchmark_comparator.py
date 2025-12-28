"""
ベンチマーク比較機能のテスト
"""

import json
from pathlib import Path
import tempfile

from docgen.benchmark import BenchmarkComparator
from docgen.benchmark.models import BenchmarkResult, BenchmarkSummary


class TestBenchmarkComparator:
    """BenchmarkComparatorのテスト"""

    def test_compare_basic(self):
        """基本的な比較機能のテスト"""
        # テストデータの作成
        baseline_results = [
            BenchmarkResult(
                name="test1",
                duration=1.0,
                memory_peak=1000,
                memory_delta=500,
            ),
            BenchmarkResult(
                name="test2",
                duration=2.0,
                memory_peak=2000,
                memory_delta=1000,
            ),
        ]

        current_results = [
            BenchmarkResult(
                name="test1",
                duration=1.2,  # 20%悪化
                memory_peak=1100,
                memory_delta=550,
            ),
            BenchmarkResult(
                name="test2",
                duration=1.8,  # 10%改善
                memory_peak=1900,
                memory_delta=950,
            ),
        ]

        baseline_summary = BenchmarkSummary(
            total_duration=3.0,
            total_results=2,
            memory_peak_total=2000,
            cpu_avg=15.0,
            results=baseline_results,
        )

        current_summary = BenchmarkSummary(
            total_duration=3.0,
            total_results=2,
            memory_peak_total=1900,
            cpu_avg=15.0,
            results=current_results,
        )

        # 一時ファイルに保存
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_path = Path(tmpdir) / "baseline.json"
            current_path = Path(tmpdir) / "current.json"

            baseline_path.write_text(
                json.dumps(baseline_summary.model_dump(mode="json"), indent=2), encoding="utf-8"
            )
            current_path.write_text(
                json.dumps(current_summary.model_dump(mode="json"), indent=2), encoding="utf-8"
            )

            comparator = BenchmarkComparator(baseline_path, current_path)
            comparison = comparator.compare()

            assert len(comparison["comparisons"]) == 2
            assert comparison["comparisons"][0]["name"] == "test1"
            assert comparison["comparisons"][0]["status"] == "regression"  # 20%悪化
            assert comparison["comparisons"][1]["name"] == "test2"
            assert comparison["comparisons"][1]["status"] == "stable"  # 10%改善は閾値以下

    def test_compare_new_and_removed(self):
        """新規追加と削除された処理の比較テスト"""
        baseline_results = [
            BenchmarkResult(
                name="test1",
                duration=1.0,
                memory_peak=1000,
                memory_delta=500,
            ),
        ]

        current_results = [
            BenchmarkResult(
                name="test2",  # 新規
                duration=2.0,
                memory_peak=2000,
                memory_delta=1000,
            ),
        ]

        baseline_summary = BenchmarkSummary(
            total_duration=1.0,
            total_results=1,
            memory_peak_total=1000,
            cpu_avg=10.0,
            results=baseline_results,
        )

        current_summary = BenchmarkSummary(
            total_duration=2.0,
            total_results=1,
            memory_peak_total=2000,
            cpu_avg=10.0,
            results=current_results,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_path = Path(tmpdir) / "baseline.json"
            current_path = Path(tmpdir) / "current.json"

            baseline_path.write_text(
                json.dumps(baseline_summary.model_dump(mode="json"), indent=2), encoding="utf-8"
            )
            current_path.write_text(
                json.dumps(current_summary.model_dump(mode="json"), indent=2), encoding="utf-8"
            )

            comparator = BenchmarkComparator(baseline_path, current_path)
            comparison = comparator.compare()

            assert len(comparison["comparisons"]) == 2
            # test1は削除された
            removed = next((c for c in comparison["comparisons"] if c["name"] == "test1"), None)
            assert removed is not None
            assert removed["status"] == "removed"

            # test2は新規追加
            new = next((c for c in comparison["comparisons"] if c["name"] == "test2"), None)
            assert new is not None
            assert new["status"] == "new"

    def test_generate_comparison_report(self):
        """比較レポート生成のテスト"""
        baseline_results = [
            BenchmarkResult(
                name="test1",
                duration=1.0,
                memory_peak=1000,
                memory_delta=500,
            ),
        ]

        current_results = [
            BenchmarkResult(
                name="test1",
                duration=1.2,
                memory_peak=1100,
                memory_delta=550,
            ),
        ]

        baseline_summary = BenchmarkSummary(
            total_duration=1.0,
            total_results=1,
            memory_peak_total=1000,
            cpu_avg=10.0,
            results=baseline_results,
        )

        current_summary = BenchmarkSummary(
            total_duration=1.2,
            total_results=1,
            memory_peak_total=1100,
            cpu_avg=10.0,
            results=current_results,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_path = Path(tmpdir) / "baseline.json"
            current_path = Path(tmpdir) / "current.json"

            baseline_path.write_text(
                json.dumps(baseline_summary.model_dump(mode="json"), indent=2), encoding="utf-8"
            )
            current_path.write_text(
                json.dumps(current_summary.model_dump(mode="json"), indent=2), encoding="utf-8"
            )

            comparator = BenchmarkComparator(baseline_path, current_path)
            report = comparator.generate_comparison_report()

            assert "ベンチマーク比較レポート" in report
            assert "test1" in report
            assert "regression" in report or "stable" in report
