"""
ベンチマーク結果のレポート生成モジュール
"""

import csv
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from .models import BenchmarkResult
from .recorder import BenchmarkRecorder
from .utils import format_duration, format_memory


class BenchmarkReporter:
    """ベンチマーク結果のレポート生成クラス"""

    def __init__(self, recorder: BenchmarkRecorder | None = None):
        """
        初期化

        Args:
            recorder: ベンチマークレコーダー（Noneの場合はグローバルレコーダーを使用）
        """
        self.recorder = recorder or BenchmarkRecorder.get_global()

    def generate_markdown(self, include_children: bool = True) -> str:
        """
        Markdown形式のレポートを生成

        Args:
            include_children: 子処理の結果を含めるかどうか

        Returns:
            Markdown形式のレポート
        """
        summary = self.recorder.get_summary()
        results = summary.results

        if not results:
            return "# ベンチマーク結果\n\n測定結果がありません。\n"

        lines = [
            "# ベンチマーク結果",
            "",
            f"**実行日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 実行概要",
            "",
            f"- 総実行時間: {format_duration(summary.total_duration)}",
            f"- 測定結果数: {summary.total_results}",
            f"- ピークメモリ使用量: {format_memory(summary.memory_peak_total)}",
            f"- 平均CPU使用率: {summary.cpu_avg:.1f}%",
            "",
            "## 処理別実行時間",
            "",
            "| 処理名 | 実行時間 | メモリ使用量 | メモリ増加 | CPU使用率 | ボトルネック |",
            "|--------|----------|--------------|------------|-----------|--------------|",
        ]

        # ボトルネックのセットを作成
        bottleneck_set = set(summary.bottlenecks)

        for result in sorted(results, key=lambda r: r.duration, reverse=True):
            is_bottleneck = "⚠️" if result.name in bottleneck_set else ""
            lines.append(
                f"| {result.name} | {format_duration(result.duration)} | "
                f"{format_memory(result.memory_peak)} | {format_memory(result.memory_delta)} | "
                f"{result.cpu_percent:.1f}% | {is_bottleneck} |"
            )

            # 子処理の表示
            if include_children and result.children:
                for child in sorted(result.children, key=lambda r: r.duration, reverse=True):
                    lines.append(
                        f"| └─ {child.name} | {format_duration(child.duration)} | "
                        f"{format_memory(child.memory_peak)} | {format_memory(child.memory_delta)} | "
                        f"{child.cpu_percent:.1f}% | |"
                    )

        lines.append("")

        # ボトルネック分析
        if summary.bottlenecks:
            lines.extend(
                [
                    "## ボトルネック分析",
                    "",
                ]
            )

            for i, bottleneck_name in enumerate(summary.bottlenecks, 1):
                bottleneck_result: BenchmarkResult | None = next((r for r in results if r.name == bottleneck_name), None)
                if bottleneck_result is not None:
                    percentage = (
                        (bottleneck_result.duration / summary.total_duration * 100)
                        if summary.total_duration > 0
                        else 0
                    )
                    lines.extend(
                        [
                            f"{i}. **{bottleneck_name}** ({format_duration(bottleneck_result.duration)}, {percentage:.1f}%)",
                            f"   - メモリ使用量: {format_memory(bottleneck_result.memory_peak)}",
                            f"   - CPU使用率: {bottleneck_result.cpu_percent:.1f}%",
                            "",
                        ]
                    )

        return "\n".join(lines)

    def generate_json(self) -> dict[str, Any]:
        """
        JSON形式のレポートを生成

        Returns:
            JSON形式の辞書
        """
        return self.recorder.export_json()

    def save_markdown(self, path: Path) -> None:
        """
        Markdownレポートをファイルに保存

        Args:
            path: 保存先のパス
        """
        content = self.generate_markdown()
        path.write_text(content, encoding="utf-8")

    def save_json(self, path: Path) -> None:
        """
        JSONレポートをファイルに保存

        Args:
            path: 保存先のパス
        """
        content = self.generate_json()
        path.write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8")

    def generate_csv(self, include_children: bool = True) -> str:
        """
        CSV形式のレポートを生成

        Args:
            include_children: 子処理の結果を含めるかどうか

        Returns:
            CSV形式の文字列
        """
        import io

        summary = self.recorder.get_summary()
        results = summary.results

        if not results:
            return ""

        output = io.StringIO()
        writer = csv.writer(output)

        # ヘッダー
        writer.writerow(
            [
                "処理名",
                "実行時間(秒)",
                "メモリ使用量(バイト)",
                "メモリ増加(バイト)",
                "CPU使用率(%)",
                "ボトルネック",
                "タイムスタンプ",
            ]
        )

        # ボトルネックのセットを作成
        bottleneck_set = set(summary.bottlenecks)

        # データ行
        for result in sorted(results, key=lambda r: r.duration, reverse=True):
            is_bottleneck = "⚠️" if result.name in bottleneck_set else ""
            writer.writerow(
                [
                    result.name,
                    f"{result.duration:.6f}",
                    result.memory_peak,
                    result.memory_delta,
                    f"{result.cpu_percent:.2f}",
                    is_bottleneck,
                    result.timestamp.isoformat(),
                ]
            )

            # 子処理の表示
            if include_children and result.children:
                for child in sorted(result.children, key=lambda r: r.duration, reverse=True):
                    writer.writerow(
                        [
                            f"  {child.name}",
                            f"{child.duration:.6f}",
                            child.memory_peak,
                            child.memory_delta,
                            f"{child.cpu_percent:.2f}",
                            "",
                            child.timestamp.isoformat(),
                        ]
                    )

        return output.getvalue()

    def save_csv(self, path: Path, include_children: bool = True) -> None:
        """
        CSVレポートをファイルに保存

        Args:
            path: 保存先のパス
            include_children: 子処理の結果を含めるかどうか
        """
        content = self.generate_csv(include_children=include_children)
        path.write_text(content, encoding="utf-8")

    def detect_bottlenecks(self, threshold_percent: float = 10.0) -> list[str]:
        """
        ボトルネックを検出

        Args:
            threshold_percent: ボトルネックとみなす実行時間の割合（%）

        Returns:
            ボトルネックの処理名のリスト
        """
        summary = self.recorder.get_summary()
        if summary.total_duration == 0:
            return []

        threshold = summary.total_duration * (threshold_percent / 100.0)
        return [r.name for r in summary.results if r.duration >= threshold]
