"""
CLI Argument Parser
"""

import argparse
from pathlib import Path


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the CLI argument parser

    Returns:
        Configured ArgumentParser instance
    """
    try:
        from .. import __version__
    except (ImportError, ValueError, SystemError):
        __version__ = "0.0.1"

    parser = argparse.ArgumentParser(
        description="汎用ドキュメント自動生成システム",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Global options
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--config", type=Path, help="設定ファイルのパス")
    parser.add_argument("--quiet", action="store_true", help="詳細メッセージを抑制")

    # Document generation options (used when no subcommand is specified)
    parser.add_argument("--detect-only", action="store_true", help="言語検出のみ実行")
    parser.add_argument("--no-api-doc", action="store_true", help="APIドキュメントを生成しない")
    parser.add_argument("--no-readme", action="store_true", help="READMEを更新しない")

    # RAG options
    parser.add_argument("--build-index", action="store_true", help="RAGインデックスをビルド")
    parser.add_argument("--use-rag", action="store_true", help="RAGを使用してドキュメント生成")

    # Architecture generation options
    parser.add_argument(
        "--generate-arch", action="store_true", help="アーキテクチャ図を生成（Mermaid形式）"
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="実行するコマンド")

    # init subcommand
    init_parser = subparsers.add_parser("init", help="プロジェクトの初期化（必須ファイルを作成）")
    init_parser.add_argument("--force", action="store_true", help="既存ファイルを強制上書き")

    # commit-msg subcommand
    subparsers.add_parser("commit-msg", help="コミットメッセージ生成")

    # hooks subcommand
    hooks_parser = subparsers.add_parser("hooks", help="Git hooksの管理")
    hooks_subparsers = hooks_parser.add_subparsers(dest="hooks_action", help="アクション")

    # hooks list
    hooks_subparsers.add_parser("list", help="利用可能なフックを表示")

    # hooks enable
    enable_parser = hooks_subparsers.add_parser("enable", help="フックを有効化")
    enable_parser.add_argument("hook_name", nargs="?", help="フック名（指定しない場合は全て）")

    # hooks disable
    disable_parser = hooks_subparsers.add_parser("disable", help="フックを無効化")
    disable_parser.add_argument("hook_name", nargs="?", help="フック名（指定しない場合は全て）")

    # hooks run
    run_parser = hooks_subparsers.add_parser("run", help="フックを手動実行")
    run_parser.add_argument("hook_name", help="実行するフック名")
    run_parser.add_argument("hook_args", nargs="*", help="フック引数")

    # hooks validate
    hooks_subparsers.add_parser("validate", help="フック設定を検証")

    # benchmark subcommand
    benchmark_parser = subparsers.add_parser(
        "benchmark", help="ベンチマークを実行してレポートを生成"
    )
    benchmark_parser.add_argument(
        "--targets",
        nargs="+",
        choices=["all", "generate", "detect", "rag"],
        default=["all"],
        help="測定対象の処理（デフォルト: all）",
    )
    benchmark_parser.add_argument(
        "--format",
        choices=["markdown", "json", "csv"],
        default="markdown",
        help="出力形式（デフォルト: markdown）",
    )
    benchmark_parser.add_argument(
        "--output", type=Path, help="出力ファイルのパス（指定しない場合は標準出力）"
    )
    benchmark_parser.add_argument("--verbose", action="store_true", help="詳細情報を表示")
    benchmark_parser.add_argument(
        "--compare",
        nargs=2,
        metavar=("BASELINE", "CURRENT"),
        help="2つのベンチマーク結果を比較（JSONファイルのパスを2つ指定）",
    )

    return parser
