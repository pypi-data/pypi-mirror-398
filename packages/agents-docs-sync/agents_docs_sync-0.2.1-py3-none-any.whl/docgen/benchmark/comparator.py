"""
ベンチマーク結果の比較機能
"""

import json
from pathlib import Path
from typing import Any

from .models import BenchmarkSummary
from .utils import format_duration, format_memory


class BenchmarkComparator:
    """ベンチマーク結果の比較クラス"""

    def __init__(self, baseline_path: Path, current_path: Path):
        """
        初期化

        Args:
            baseline_path: ベースライン（比較元）のJSONファイルパス
            current_path: 現在の（比較先）のJSONファイルパス
        """
        self.baseline_path = baseline_path
        self.current_path = current_path
        self.baseline_data = self._load_json(baseline_path)
        self.current_data = self._load_json(current_path)

    def _load_json(self, path: Path) -> dict[str, Any]:
        """
        JSONファイルを読み込む

        Args:
            path: JSONファイルのパス

        Returns:
            読み込んだデータ
        """
        if not path.exists():
            raise FileNotFoundError(f"ファイルが見つかりません: {path}")

        content = path.read_text(encoding="utf-8")
        return json.loads(content)

    def compare(self) -> dict[str, Any]:
        """
        ベンチマーク結果を比較

        Returns:
            比較結果の辞書
        """
        baseline_summary = BenchmarkSummary(**self.baseline_data)
        current_summary = BenchmarkSummary(**self.current_data)

        # 処理名でマッピングを作成
        baseline_map = {r.name: r for r in baseline_summary.results}
        current_map = {r.name: r for r in current_summary.results}

        # 比較結果
        comparisons = []
        all_names = set(baseline_map.keys()) | set(current_map.keys())

        for name in sorted(all_names):
            baseline_result = baseline_map.get(name)
            current_result = current_map.get(name)

            if baseline_result is None:
                # 新規追加された処理
                if current_result is None:
                    continue
                comparisons.append(
                    {
                        "name": name,
                        "status": "new",
                        "baseline_duration": None,
                        "current_duration": current_result.duration,
                        "duration_diff": current_result.duration,
                        "duration_diff_percent": 100.0,
                        "memory_diff": current_result.memory_peak - 0,
                        "memory_diff_percent": 100.0,
                    }
                )
            elif current_result is None:
                # 削除された処理
                comparisons.append(
                    {
                        "name": name,
                        "status": "removed",
                        "baseline_duration": baseline_result.duration,
                        "current_duration": None,
                        "duration_diff": -baseline_result.duration,
                        "duration_diff_percent": -100.0,
                        "memory_diff": 0 - baseline_result.memory_peak,
                        "memory_diff_percent": -100.0,
                    }
                )
            else:
                # 両方に存在する処理
                duration_diff = current_result.duration - baseline_result.duration
                duration_diff_percent = (
                    (duration_diff / baseline_result.duration * 100)
                    if baseline_result.duration > 0
                    else 0.0
                )

                memory_diff = current_result.memory_peak - baseline_result.memory_peak
                memory_diff_percent = (
                    (memory_diff / baseline_result.memory_peak * 100)
                    if baseline_result.memory_peak > 0
                    else 0.0
                )

                # パフォーマンス回帰の判定（10%以上の悪化）
                status = (
                    "regression"
                    if duration_diff_percent > 10.0
                    else "improved"
                    if duration_diff_percent < -10.0
                    else "stable"
                )

                comparisons.append(
                    {
                        "name": name,
                        "status": status,
                        "baseline_duration": baseline_result.duration,
                        "current_duration": current_result.duration,
                        "duration_diff": duration_diff,
                        "duration_diff_percent": duration_diff_percent,
                        "memory_diff": memory_diff,
                        "memory_diff_percent": memory_diff_percent,
                    }
                )

        baseline_timestamp = (
            baseline_summary.results[0].timestamp.isoformat()
            if baseline_summary.results and baseline_summary.results[0].timestamp
            else None
        )
        current_timestamp = (
            current_summary.results[0].timestamp.isoformat()
            if current_summary.results and current_summary.results[0].timestamp
            else None
        )

        return {
            "baseline": {
                "total_duration": baseline_summary.total_duration,
                "memory_peak": baseline_summary.memory_peak_total,
                "timestamp": baseline_timestamp,
            },
            "current": {
                "total_duration": current_summary.total_duration,
                "memory_peak": current_summary.memory_peak_total,
                "timestamp": current_timestamp,
            },
            "comparisons": comparisons,
            "regressions": [c for c in comparisons if c["status"] == "regression"],
            "improvements": [c for c in comparisons if c["status"] == "improved"],
        }

    def generate_comparison_report(self) -> str:
        """
        比較レポートをMarkdown形式で生成

        Returns:
            Markdown形式のレポート
        """
        comparison = self.compare()

        lines = [
            "# ベンチマーク比較レポート",
            "",
            "## 概要",
            "",
            f"**ベースライン**: {self.baseline_path.name}",
            f"  - 総実行時間: {format_duration(comparison['baseline']['total_duration'])}",
            f"  - ピークメモリ: {format_memory(comparison['baseline']['memory_peak'])}",
            "",
            f"**現在**: {self.current_path.name}",
            f"  - 総実行時間: {format_duration(comparison['current']['total_duration'])}",
            f"  - ピークメモリ: {format_memory(comparison['current']['memory_peak'])}",
            "",
            "## 比較結果",
            "",
            "| 処理名 | ベースライン | 現在 | 差分 | 差分(%) | ステータス |",
            "|--------|-------------|------|------|---------|-----------|",
        ]

        for comp in comparison["comparisons"]:
            baseline_str = (
                format_duration(comp["baseline_duration"])
                if comp["baseline_duration"] is not None
                else "-"
            )
            current_str = (
                format_duration(comp["current_duration"])
                if comp["current_duration"] is not None
                else "-"
            )
            diff_str = (
                format_duration(comp["duration_diff"]) if comp["duration_diff"] != 0 else "0s"
            )
            diff_percent_str = f"{comp['duration_diff_percent']:+.1f}%"

            # ステータス表示
            status_icon = {
                "regression": "🔴",
                "improved": "🟢",
                "stable": "🟡",
                "new": "🆕",
                "removed": "❌",
            }.get(comp["status"], "❓")

            lines.append(
                f"| {comp['name']} | {baseline_str} | {current_str} | {diff_str} | {diff_percent_str} | {status_icon} {comp['status']} |"
            )

        lines.append("")

        # パフォーマンス回帰
        if comparison["regressions"]:
            lines.extend(
                [
                    "## ⚠️ パフォーマンス回帰",
                    "",
                ]
            )
            for reg in comparison["regressions"]:
                lines.append(
                    f"- **{reg['name']}**: {format_duration(reg['baseline_duration'])} → "
                    f"{format_duration(reg['current_duration'])} "
                    f"({reg['duration_diff_percent']:+.1f}% 悪化)"
                )
            lines.append("")

        # 改善
        if comparison["improvements"]:
            lines.extend(
                [
                    "## ✅ パフォーマンス改善",
                    "",
                ]
            )
            for imp in comparison["improvements"]:
                lines.append(
                    f"- **{imp['name']}**: {format_duration(imp['baseline_duration'])} → "
                    f"{format_duration(imp['current_duration'])} "
                    f"({imp['duration_diff_percent']:+.1f}% 改善)"
                )
            lines.append("")

        return "\n".join(lines)

    def save_comparison_report(self, path: Path) -> None:
        """
        比較レポートをファイルに保存

        Args:
            path: 保存先のパス
        """
        content = self.generate_comparison_report()
        path.write_text(content, encoding="utf-8")
