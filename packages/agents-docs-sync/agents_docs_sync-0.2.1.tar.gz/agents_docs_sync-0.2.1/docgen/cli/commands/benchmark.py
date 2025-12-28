"""
Benchmark command - Run benchmarks and generate reports
"""

from argparse import Namespace
from pathlib import Path

from ...benchmark import BenchmarkComparator, BenchmarkRecorder, BenchmarkReporter
from ...utils.logger import get_logger
from .base import BaseCommand

logger = get_logger("docgen.cli.benchmark")


class BenchmarkCommand(BaseCommand):
    """ベンチマークコマンド"""

    def execute(self, args: Namespace, project_root: Path) -> int:
        """
        Run benchmarks and generate reports

        Args:
            args: Command line arguments
            project_root: Project root directory

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        # 比較モードの処理
        compare_files = getattr(args, "compare", None)
        if compare_files and len(compare_files) == 2:
            return self._handle_compare_mode(compare_files, project_root)

        from ... import DocGen

        # ベンチマークを有効化
        config_updates = {"benchmark.enabled": True}

        # Initialize DocGen
        config_path = getattr(args, "config", None)
        docgen = DocGen(project_root=project_root, config_path=config_path)
        docgen.update_config(config_updates)

        # レコーダーをリセット
        BenchmarkRecorder.reset_global()
        recorder = BenchmarkRecorder.get_global()

        # 測定対象の決定
        targets = getattr(args, "targets", None) or []
        if not targets:
            # デフォルト: 全ての処理を測定
            targets = ["all"]

        # ベンチマーク実行
        try:
            if "all" in targets or "generate" in targets:
                logger.info("ドキュメント生成のベンチマークを実行中...")
                success = docgen.generate_documents()
                if not success:
                    logger.warning(
                        "ドキュメント生成中にエラーが発生しましたが、ベンチマークは続行します"
                    )

            # 結果の取得
            results = recorder.get_results()
            if not results:
                logger.warning("ベンチマーク結果が記録されていません")
                return 1

            # レポート生成
            reporter = BenchmarkReporter(recorder)
            output_format = getattr(args, "format", "markdown")
            output_path = getattr(args, "output", None)
            verbose = getattr(args, "verbose", False)

            if output_format == "json":
                if output_path:
                    path = Path(output_path)
                    reporter.save_json(path)
                    logger.info(f"JSONレポートを保存しました: {path}")
                else:
                    import json

                    content = reporter.generate_json()
                    print(json.dumps(content, indent=2, ensure_ascii=False))
            elif output_format == "csv":
                if output_path:
                    path = Path(output_path)
                    reporter.save_csv(path)
                    logger.info(f"CSVレポートを保存しました: {path}")
                else:
                    csv_content = reporter.generate_csv()
                    print(csv_content)
            else:  # markdown
                if output_path:
                    path = Path(output_path)
                    reporter.save_markdown(path)
                    logger.info(f"Markdownレポートを保存しました: {path}")
                else:
                    # 標準出力に表示
                    markdown = reporter.generate_markdown()
                    print("\n" + markdown)

            # ボトルネックの表示
            bottlenecks = reporter.detect_bottlenecks()
            if bottlenecks:
                logger.info("\n⚠️  ボトルネックが検出されました:")
                for bottleneck in bottlenecks:
                    logger.info(f"  - {bottleneck}")

            # 詳細情報の表示（verboseモード）
            if verbose:
                summary = recorder.get_summary()
                logger.info("\n詳細情報:")
                logger.info(f"  総実行時間: {summary.total_duration:.2f}秒")
                logger.info(f"  ピークメモリ: {summary.memory_peak_total / 1024 / 1024:.2f} MB")
                logger.info(f"  平均CPU使用率: {summary.cpu_avg:.1f}%")
                logger.info(f"  測定結果数: {summary.total_results}")

            return 0

        except Exception as e:
            logger.error(f"ベンチマーク実行中にエラーが発生しました: {e}", exc_info=True)
            return 1

    def _handle_compare_mode(self, compare_files: list[str], project_root: Path) -> int:
        """
        比較モードの処理

        Args:
            compare_files: 比較する2つのJSONファイルパス
            project_root: プロジェクトルートディレクトリ

        Returns:
            終了コード
        """
        try:
            baseline_path = Path(compare_files[0]).resolve()
            current_path = Path(compare_files[1]).resolve()

            if not baseline_path.exists():
                logger.error(f"ベースラインファイルが見つかりません: {baseline_path}")
                return 1

            if not current_path.exists():
                logger.error(f"現在のファイルが見つかりません: {current_path}")
                return 1

            comparator = BenchmarkComparator(baseline_path, current_path)
            report = comparator.generate_comparison_report()

            print("\n" + report)

            # パフォーマンス回帰がある場合は警告
            comparison = comparator.compare()
            if comparison["regressions"]:
                logger.warning(
                    f"\n⚠️  {len(comparison['regressions'])} 件のパフォーマンス回帰が検出されました"
                )
                return 1

            return 0

        except Exception as e:
            logger.error(f"比較処理中にエラーが発生しました: {e}", exc_info=True)
            return 1
