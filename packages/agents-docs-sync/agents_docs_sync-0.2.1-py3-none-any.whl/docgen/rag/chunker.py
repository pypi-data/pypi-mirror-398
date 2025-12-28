"""コードベースのチャンク化モジュール

コードベースを意味のある単位（関数、クラス、セクション）に分割し、
RAGインデックス用のチャンクを生成します。
"""

from pathlib import Path
import re
from typing import Any

from ..utils.logger import get_logger

logger = get_logger(__name__)


class CodeChunker:
    """コードベースをチャンク化するクラス"""

    # 機密情報を含む可能性があるパターン
    DEFAULT_EXCLUDE_PATTERNS = [
        r".*\.env$",
        r"secrets/.*",
        r".*_SECRET.*",
        r".*API_KEY.*",
        r".*password.*",
        r".*token.*\.json$",
    ]

    # 無視すべきディレクトリ（セットで高速検索）
    IGNORE_DIRS = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
        ".idea",
        ".vscode",
        "dist",
        "build",
        "coverage",
        "docgen/index",  # インデックスディレクトリ自体を除外
    }

    # 除外ディレクトリを分類（効率化のため）
    _exact_dir_names: set[str] = set()  # 完全一致チェック用
    _path_patterns: set[str] = set()  # パスパターンチェック用

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初期化

        Args:
            config: RAG設定（config.toml の rag セクション）
        """
        self.config = config or {}
        self.max_chunk_size = self.config.get("chunking", {}).get("max_chunk_size", 512)
        self.overlap = self.config.get("chunking", {}).get("overlap", 50)

        # カスタム除外パターン + デフォルトパターン
        custom_patterns = self.config.get("exclude_patterns", [])
        self.exclude_patterns = self.DEFAULT_EXCLUDE_PATTERNS + custom_patterns

        # 除外ファイル名リスト
        self.exclude_files = self.config.get("exclude_files", ["README.md", "AGENTS.md"])

        # 除外ディレクトリを分類（効率化のため）
        if not self._exact_dir_names:  # クラス変数の初期化（一度だけ）
            for d in self.IGNORE_DIRS:
                if "/" not in d:
                    self._exact_dir_names.add(d)
                else:
                    self._path_patterns.add(d)

    def should_process_file(self, file_path: Path) -> bool:
        """
        ファイルを処理すべきかどうかを判定

        Args:
            file_path: ファイルパス

        Returns:
            処理すべき場合True
        """
        str_path = str(file_path)

        # 除外パターンのチェック
        for pattern in self.exclude_patterns:
            if re.search(pattern, str_path):
                return False

        # 除外ファイル名のチェック
        if file_path.name in self.exclude_files:
            return False

        # バイナリファイルやテストファイルは除外
        excluded_suffixes = {".pyc", ".pyo", ".so", ".dylib", ".whl", ".egg"}
        if file_path.suffix in excluded_suffixes:
            return False

        # 一般的な除外ディレクトリ（.venv, .git, node_modules等）
        excluded_dirs = {
            ".venv",
            "venv",
            ".git",
            ".hg",
            ".svn",
            "node_modules",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            ".tox",
            "dist",
            "build",
            ".eggs",
            "*.egg-info",
            ".cache",
            "htmlcov",
            ".coverage",
            ".DS_Store",
        }

        # パスに除外ディレクトリが含まれているかチェック
        path_parts = file_path.parts
        for part in path_parts:
            if part in excluded_dirs or part.startswith("."):
                # ただし、プロジェクトルート直下の設定ファイル（.github等）は許可
                if len(path_parts) == 2 and part.startswith(".") and file_path.is_file():
                    continue
                return False

        # テストファイルを除外
        name_lower = file_path.name.lower()
        if (
            name_lower.startswith("test_")
            or name_lower.endswith("_test.py")
            or ".test." in name_lower
            or ".spec." in name_lower
            or name_lower.startswith("test.")
            or name_lower.startswith("spec.")
        ):
            return False
        if "tests" in path_parts or "test" in path_parts or "__tests__" in path_parts:
            return False

        return True

    def chunk_file(self, file_path: Path, project_root: Path) -> list[dict[str, Any]]:
        """
        ファイルをチャンク化

        Args:
            file_path: ファイルパス
            project_root: プロジェクトルート

        Returns:
            チャンクのリスト
        """
        if not self.should_process_file(file_path):
            return []

        try:
            content = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError) as e:
            logger.warning(f"Failed to read file {file_path}: {e}")
            return []

        # Initialize strategies
        from docgen.detectors.detector_patterns import DetectorPatterns

        from .strategies import CodeChunkStrategy, MarkdownChunkStrategy, TextChunkStrategy

        code_strategy = CodeChunkStrategy(project_root)
        markdown_strategy = MarkdownChunkStrategy(project_root)
        text_strategy = TextChunkStrategy(project_root)

        # 全言語の拡張子セットを取得
        code_extensions = set()
        for exts in DetectorPatterns.SOURCE_EXTENSIONS.values():
            code_extensions.update(exts)

        # Dispatch to appropriate strategy
        if file_path.suffix.lower() in code_extensions or file_path.suffix.lower() in {
            ".yaml",
            ".yml",
            ".toml",
        }:
            return code_strategy.chunk(content, file_path)
        elif file_path.suffix.lower() == ".md":
            return markdown_strategy.chunk(content, file_path)
        else:
            return text_strategy.chunk(content, file_path)

    def chunk_codebase(
        self, project_root: Path, allowed_patterns: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """
        プロジェクト全体をチャンク化

        Args:
            project_root: プロジェクトルート
            allowed_patterns: 許可するファイルパターンのリスト（Noneの場合はすべて許可/設定依存）

        Returns:
            すべてのチャンクのリスト
        """
        all_chunks = []

        # os.walkを使用してディレクトリを走査し、無視すべきディレクトリをスキップ
        import os

        for root, dirs, files in os.walk(project_root):
            # 無視すべきディレクトリを削除（in-place変更でos.walkの探索を制御）
            # 相対パスでチェックする必要があるため、少し工夫が必要
            # ここでは単純なディレクトリ名チェックと、パスチェックを行う

            # 1. ディレクトリ名でフィルタリング（O(1)のセット検索）
            dirs[:] = [d for d in dirs if d not in self._exact_dir_names and not d.startswith(".")]

            # 2. パスベースのフィルタリング（docgen/indexのようなネストされたパス用）
            # os.walkのdirsはディレクトリ名のみなので、ここで削除するとその下には行かない
            # ただし、docgen/indexのようなパスはここだけでは判定しにくい場合がある
            # 親ディレクトリ(root)と結合してチェック

            valid_dirs = []
            for d in dirs:
                dir_path = Path(root) / d
                try:
                    rel_path = dir_path.relative_to(project_root)
                    rel_str = str(rel_path)

                    # 完全一致チェック（O(1)）
                    if rel_str in self.IGNORE_DIRS:
                        continue

                    # パスパターンチェック（必要な場合のみ）
                    if self._path_patterns:
                        for pattern in self._path_patterns:
                            if rel_str.startswith(pattern):
                                continue
                except ValueError:
                    # プロジェクトルート外の場合はスキップ
                    continue

                valid_dirs.append(d)
            dirs[:] = valid_dirs

            for file_name in files:
                file_path = Path(root) / file_name
                if self.should_process_file(file_path):
                    # パターンフィルタリング（指定されている場合）
                    if allowed_patterns:
                        try:
                            # pathlib.matchはglobパターンを使用
                            # 再帰的なパターンやディレクトリを含まない場合はファイル名に対してマッチ
                            if not any(file_path.match(p) for p in allowed_patterns):
                                continue
                        except Exception:
                            continue

                    chunks = self.chunk_file(file_path, project_root)
                    all_chunks.extend(chunks)

        logger.info(f"Created {len(all_chunks)} chunks from codebase")
        return all_chunks
