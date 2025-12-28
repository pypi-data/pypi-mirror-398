"""
汎用ドキュメント自動生成システム

GitHubにプッシュされた変更をトリガーに、テスト実行・ドキュメント生成・AGENTS.mdの自動更新を行うパイプライン
"""

import importlib.metadata

try:
    __version__ = importlib.metadata.version(
        __package__ if __package__ not in ["docgen", "agents_docs_sync"] else "agents-docs-sync"
    )
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"

from .docgen import DocGen, main

__all__ = ["DocGen", "main"]
