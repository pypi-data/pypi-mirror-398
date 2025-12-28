"""
ベンチマーク結果の記録と集計を行うモジュール
"""

from typing import Any

from .models import BenchmarkResult, BenchmarkSummary


class BenchmarkRecorder:
    """ベンチマーク結果の記録と集計を行うクラス"""

    _global_instance: "BenchmarkRecorder | None" = None

    def __init__(self):
        """初期化"""
        self._results: list[BenchmarkResult] = []

    @classmethod
    def get_global(cls) -> "BenchmarkRecorder":
        """
        グローバルレコーダーインスタンスを取得

        Returns:
            グローバルレコーダーインスタンス
        """
        if cls._global_instance is None:
            cls._global_instance = cls()
        return cls._global_instance

    @classmethod
    def reset_global(cls) -> None:
        """グローバルレコーダーをリセット"""
        cls._global_instance = None

    def record(self, result: BenchmarkResult) -> None:
        """
        ベンチマーク結果を記録

        Args:
            result: ベンチマーク結果
        """
        self._results.append(result)

    def get_results(self) -> list[BenchmarkResult]:
        """
        記録された結果を取得

        Returns:
            ベンチマーク結果のリスト
        """
        return self._results.copy()

    def clear(self) -> None:
        """記録をクリア"""
        self._results.clear()

    def get_summary(self) -> BenchmarkSummary:
        """
        ベンチマーク結果の集計情報を取得

        Returns:
            ベンチマーク集計情報
        """
        if not self._results:
            return BenchmarkSummary(
                total_duration=0.0,
                total_results=0,
                memory_peak_total=0,
                cpu_avg=0.0,
            )

        total_duration = sum(r.duration for r in self._results)
        total_results = len(self._results)
        memory_peak_total = max((r.memory_peak for r in self._results), default=0)
        cpu_values = [r.cpu_percent for r in self._results if r.cpu_percent > 0]
        cpu_avg = sum(cpu_values) / len(cpu_values) if cpu_values else 0.0

        # ボトルネックの検出（実行時間が全体の10%以上を占める処理）
        threshold = total_duration * 0.1
        bottlenecks = [r.name for r in self._results if r.duration >= threshold]

        return BenchmarkSummary(
            total_duration=total_duration,
            total_results=total_results,
            memory_peak_total=memory_peak_total,
            cpu_avg=cpu_avg,
            results=self._results.copy(),
            bottlenecks=bottlenecks,
        )

    def export_json(self) -> dict[str, Any]:
        """
        結果をJSON形式でエクスポート

        Returns:
            JSON形式の辞書
        """
        summary = self.get_summary()
        return summary.model_dump(mode="json")
