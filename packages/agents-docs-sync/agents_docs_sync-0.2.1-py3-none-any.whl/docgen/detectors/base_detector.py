"""
言語検出のベースクラス
"""

from abc import ABC, abstractmethod
from pathlib import Path

from .detector_patterns import DetectorPatterns


class BaseDetector(ABC):
    """言語検出のベースクラス"""

    def __init__(self, project_root: Path):
        """
        初期化

        Args:
            project_root: プロジェクトのルートディレクトリ
        """
        self.project_root: Path = project_root

    @abstractmethod
    def detect(self) -> bool:
        """
        言語が使用されているか検出

        Returns:
            検出された場合True
        """
        pass

    @abstractmethod
    def get_language(self) -> str:
        """
        検出された言語名を返す

        Returns:
            言語名（例: 'python', 'javascript'）
        """
        pass

    @abstractmethod
    def detect_package_manager(self) -> str | None:
        """
        使用されているパッケージマネージャを検出

        Returns:
            パッケージマネージャ名（例: 'pip', 'npm', 'yarn'）またはNone
        """
        pass

    def _file_exists(self, *paths) -> bool:
        """
        ファイルの存在を確認

        Args:
            *paths: 確認するファイルパス（相対パス）

        Returns:
            いずれかのファイルが存在する場合True
        """
        for path in paths:
            if (self.project_root / path).exists():
                return True
        return False

    def _has_files_with_ext(self, *extensions) -> bool:
        """
        指定された拡張子のファイルが存在するか確認

        Args:
            *extensions: 拡張子（例: '.py', '.js'）

        Returns:
            該当ファイルが存在する場合True
        """
        return DetectorPatterns.detect_by_extensions_with_exclusions(
            self.project_root, list(extensions)
        )

    def _detect_by_extensions(self, language: str) -> bool:
        """
        指定言語のソースファイル拡張子で検出

        Args:
            language: 言語名

        Returns:
            該当ファイルが存在する場合True
        """
        return DetectorPatterns.detect_by_source_files_with_exclusions(self.project_root, language)

    def _detect_by_package_files(self, language: str) -> bool:
        """
        指定言語のパッケージマネージャーファイルで検出

        Args:
            language: 言語名

        Returns:
            該当ファイルが存在する場合True
        """
        return DetectorPatterns.detect_by_package_files(self.project_root, language)

    def _has_files_in_dir(self, directory: str, *extensions, exclude_config: bool = False) -> bool:
        """
        特定ディレクトリ内のファイル存在確認

        Args:
            directory: ディレクトリ名
            *extensions: 拡張子
            exclude_config: 設定ファイルを除外する場合True

        Returns:
            該当ファイルが存在する場合True
        """
        dir_path = self.project_root / directory
        if not dir_path.exists():
            return False

        for ext in extensions:
            try:
                for file_path in dir_path.rglob(f"*{ext}"):
                    if exclude_config and DetectorPatterns.is_js_config_or_test(file_path):
                        continue
                    return True
            except (OSError, PermissionError):
                continue
        return False

    def _has_files_in_root(self, *extensions, exclude_config: bool = False) -> bool:
        """
        プロジェクトルート直下のファイル存在確認

        Args:
            *extensions: 拡張子
            exclude_config: 設定ファイルを除外する場合True

        Returns:
            該当ファイルが存在する場合True
        """
        for ext in extensions:
            try:
                for file_path in self.project_root.glob(f"*{ext}"):
                    if exclude_config and DetectorPatterns.is_js_config_or_test(file_path):
                        continue
                    return True
            except (OSError, PermissionError):
                continue
        return False
