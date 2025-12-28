#!/usr/bin/env python3
"""
汎用ドキュメント自動生成システム
コミット時にAPIドキュメントとREADME.mdを自動更新します。
"""

from pathlib import Path
import sys
from typing import Any

# プロジェクトルートのパスを取得
DOCGEN_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = DOCGEN_DIR.parent

# 相対インポートを使用（パッケージとしてインストールされている場合も動作）
from .benchmark import BenchmarkContext
from .cli import CommandRunner, create_parser
from .config_manager import ConfigManager
from .document_generator import DocumentGenerator
from .language_detector import LanguageDetector
from .models import DetectedLanguage
from .utils.logger import get_logger

# ロガーの初期化
logger = get_logger("docgen")


class DocGen:
    """ドキュメント自動生成メインクラス"""

    def __init__(self, project_root: Path | None = None, config_path: Path | None = None):
        """
        初期化

        Args:
            project_root: プロジェクトのルートディレクトリ（Noneの場合は現在の作業ディレクトリ）
            config_path: 設定ファイルのパス（Noneの場合はデフォルト）
        """
        # プロジェクトルートの決定
        # パッケージとしてインストールされた場合、実行時のカレントディレクトリを使用
        if project_root is None:
            self.project_root = Path.cwd().resolve()
        else:
            if not project_root or str(project_root) == ".":
                raise ValueError("プロジェクトルートが無効です")
            resolved_root = Path(project_root).resolve()
            self.project_root = resolved_root

        # docgenディレクトリはプロジェクトルート内のdocgenディレクトリ
        self.docgen_dir = self.project_root / "docgen"

        # パッケージ内のconfig.toml.sampleを参照するためのパス
        package_config_sample = DOCGEN_DIR / "config.toml.sample"

        self.config_path = config_path or self.docgen_dir / "config.toml"

        self.config_manager = ConfigManager(
            self.project_root, self.docgen_dir, self.config_path, package_config_sample
        )
        self.config = self.config_manager.get_config()
        self.config = self.config_manager.get_config()
        self.language_detector = LanguageDetector(self.project_root, self.config_manager)
        self.detected_languages: list[DetectedLanguage] = []
        self.detected_package_managers: dict[str, Any] = {}

    def detect_languages(self, use_parallel: bool = True) -> list[DetectedLanguage]:
        """
        プロジェクトの使用言語を自動検出

        Args:
            use_parallel: 並列処理を使用するかどうか（デフォルト: True）

        Returns:
            検出された言語オブジェクトのリスト
        """
        benchmark_enabled = self.config.get("benchmark", {}).get("enabled", False)
        with BenchmarkContext("言語検出", enabled=benchmark_enabled):
            self.detected_languages = self.language_detector.detect_languages(use_parallel)
            self.detected_package_managers = self.language_detector.detected_package_managers
        return self.detected_languages

    def update_config(self, updates: dict[str, Any]) -> None:
        """
        設定を動的に更新

        Args:
            updates: 更新する設定辞書（ドット記法対応、例: {'generation.update_readme': False}）
        """
        self.config_manager.update_config(updates)
        self.config = self.config_manager.get_config()

    def generate_documents(self) -> bool:
        """
        ドキュメントを生成

        Returns:
            成功したかどうか
        """
        benchmark_enabled = self.config.get("benchmark", {}).get("enabled", False)
        with BenchmarkContext("ドキュメント生成全体", enabled=benchmark_enabled):
            self.detect_languages()
            logger.info(f"Detected languages: {[lang.name for lang in self.detected_languages]}")

            if not self.detected_languages:
                logger.warning("サポートされている言語が検出されませんでした")
                return False

            document_generator = DocumentGenerator(
                self.project_root,
                self.detected_languages,
                self.config,
                self.detected_package_managers,
            )
            return document_generator.generate_documents()


def _check_and_auto_init(project_root: Path) -> int:
    """
    必須ファイルがない場合に自動初期化

    Args:
        project_root: Project root directory

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    from argparse import Namespace

    from .cli.commands.init import InitCommand

    config_path = project_root / "docgen" / "config.toml"

    if not config_path.exists():
        logger.info("必須ファイルが見つかりません。初期化を実行します...")

        # Create minimal args for InitCommand
        args = Namespace(force=True, quiet=True)
        init_command = InitCommand()
        result = init_command.execute(args, project_root)

        if result == 0:
            logger.info("✓ 初期化が完了しました")
        return result

    return 0


def run_cli() -> int:
    """
    Run the command line interface

    Returns:
        Exit code
    """
    parser = create_parser()
    args = parser.parse_args()

    # Determine project root
    project_root = Path.cwd().resolve()

    # Handle auto-initialization for commands that need it
    # (skip for 'init' command itself)
    if args.command != "init":
        auto_init_result = _check_and_auto_init(project_root)
        if auto_init_result != 0:
            return auto_init_result

    # Execute the command
    runner = CommandRunner()
    return runner.run(args, project_root)


def main():
    """メインエントリーポイント"""
    try:
        sys.exit(run_cli())
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
