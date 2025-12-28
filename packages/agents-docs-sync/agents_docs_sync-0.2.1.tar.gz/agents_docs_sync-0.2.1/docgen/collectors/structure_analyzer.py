"""
プロジェクト構造分析モジュール

プロジェクト内のディレクトリとファイルを分析し、
構造化された情報を提供します。
"""

import ast
from pathlib import Path
from typing import Any

from .base_collector import BaseCollector


class StructureAnalyzer(BaseCollector[dict[str, Any]]):
    """プロジェクト構造分析クラス"""

    # デフォルトの除外ディレクトリ
    DEFAULT_IGNORE_DIRS = {
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
        "htmlcov",
        ".pytest_cache",
        ".mypy_cache",
        ".tox",
    }

    # ネストしないディレクトリ（中身を展開しない）
    NO_NEST_DIRS = {
        "docs",
        "tests",
        "test",
        "__tests__",
        "scripts",
        "examples",
        "fixtures",
        "migrations",
    }

    # 構造に含める設定ファイルの拡張子
    CONFIG_EXTENSIONS = {".md", ".yaml", ".yml", ".toml", ".json", ".txt", ".sh"}

    def __init__(
        self,
        project_root: Path,
        logger: Any | None = None,
        exclude_directories: list[str] | None = None,
    ):
        """
        初期化

        Args:
            project_root: プロジェクトのルートディレクトリ
            logger: ロガーインスタンス
            exclude_directories: 除外するディレクトリのリスト（追加分）
        """
        super().__init__(project_root, logger)
        # カスタム除外ディレクトリをデフォルトに追加
        self.ignore_dirs = self.DEFAULT_IGNORE_DIRS.copy()
        if exclude_directories:
            self.ignore_dirs.update(exclude_directories)

    def collect(self, max_depth: int = 3) -> dict[str, Any]:
        """
        プロジェクト構造を収集（BaseCollectorインターフェース実装）

        Args:
            max_depth: ディレクトリの最大探索深度

        Returns:
            プロジェクト構造の辞書
        """
        return self.analyze(max_depth=max_depth)

    def count_symbols_in_file(self, file_path: Path) -> int:
        """
        Pythonファイルのシンボル数をカウント

        Args:
            file_path: Pythonファイルのパス

        Returns:
            シンボル数（クラス、関数、非同期関数の合計）
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
            return len(
                [
                    node
                    for node in ast.walk(tree)
                    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                ]
            )
        except Exception:
            return 0

    def collect_directory_structure(
        self, directory: Path, max_depth: int = 3, current_depth: int = 0
    ) -> dict[str, Any] | str:
        """
        ディレクトリ構造を再帰的に収集

        Args:
            directory: 対象ディレクトリ
            max_depth: 最大探索深度
            current_depth: 現在の深度

        Returns:
            ディレクトリ構造の辞書、またはネストしないディレクトリの場合は "directory"
        """
        if current_depth >= max_depth:
            return {}

        # exclude設定を最優先でチェック
        if directory.name in self.ignore_dirs:
            return {}

        # ネストしないディレクトリの場合は中身を展開しない
        if directory.name in self.NO_NEST_DIRS:
            return "directory"

        result = {}

        try:
            items = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name))

            for item in items:
                # exclude設定を最優先でチェック
                if item.name in self.ignore_dirs or item.name.startswith("."):
                    continue

                if item.is_dir():
                    # ネストしないディレクトリかチェック（exclude設定の後でチェック）
                    if item.name in self.NO_NEST_DIRS:
                        result[f"{item.name}/"] = "directory"
                    else:
                        # ディレクトリの場合は再帰的に処理
                        subdir_structure = self.collect_directory_structure(
                            item, max_depth, current_depth + 1
                        )
                        if subdir_structure:
                            result[f"{item.name}/"] = subdir_structure  # type: ignore[assignment]
                elif item.is_file():
                    # ファイルの場合
                    if item.suffix == ".py":
                        # Pythonファイルはシンボル数をチェック
                        symbol_count = self.count_symbols_in_file(item)
                        if symbol_count > 5:  # 重要なファイルのみ
                            result[item.name] = "file"
                    elif item.suffix in self.CONFIG_EXTENSIONS:
                        # 設定・ドキュメントファイル
                        result[item.name] = "file"

        except Exception as e:
            self.logger.debug(f"Failed to collect directory structure for {directory}: {e}")

        return result

    def analyze(self, max_depth: int = 3) -> dict[str, Any]:
        """
        プロジェクト構造を分析

        Args:
            max_depth: ディレクトリの最大探索深度

        Returns:
            プロジェクト構造の辞書
        """
        structure = {}

        try:
            items = sorted(self.project_root.iterdir(), key=lambda x: (not x.is_dir(), x.name))

            for item in items:
                # exclude設定を最優先でチェック
                if item.name in self.ignore_dirs or item.name.startswith("."):
                    continue

                if item.is_dir():
                    # ネストしないディレクトリかチェック（exclude設定の後でチェック）
                    if item.name in self.NO_NEST_DIRS:
                        structure[f"{item.name}/"] = "directory"
                    else:
                        # ディレクトリの場合
                        dir_structure = self.collect_directory_structure(item, max_depth=max_depth)
                        if dir_structure:
                            structure[f"{item.name}/"] = dir_structure  # type: ignore[assignment]

                elif item.is_file():
                    # ルートのファイル
                    if item.suffix == ".py":
                        symbol_count = self.count_symbols_in_file(item)
                        if symbol_count > 5:
                            structure[item.name] = "file"
                    elif item.suffix in self.CONFIG_EXTENSIONS:
                        structure[item.name] = "file"

        except Exception as e:
            self.logger.warning(f"Failed to collect project structure: {e}")

        return structure
