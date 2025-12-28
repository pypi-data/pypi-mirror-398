"""
統一言語検出モジュール

すべての言語をパターンベースで検出する統一Detector。
個別の言語 detector を置き換えます。
"""

from pathlib import Path
from typing import Any

from ..models import DetectedLanguage
from .base_detector import BaseDetector
from .detector_patterns import DetectorPatterns


class UnifiedDetector(BaseDetector):
    """パターンベースの統一言語検出クラス

    DetectorPatterns で定義されたすべての言語を検出します。
    """

    def __init__(self, project_root: Path, language: str):
        """
        初期化

        Args:
            project_root: プロジェクトのルートディレクトリ
            language: 検出対象の言語名
        """
        super().__init__(project_root)
        self.language = language
        self._detected: bool | None = None  # キャッシュ用

    def detect(self) -> bool:
        """
        指定された言語が使用されているか検出

        Returns:
            検出された場合True
        """
        if self._detected is not None:
            return self._detected

        # 1. パッケージマネージャーファイルの存在確認
        if self._detect_by_package_files(self.language):
            self._detected = True
            return True

        # 2. ソースファイルの存在確認（除外ディレクトリを考慮）
        if self._detect_by_extensions(self.language):
            self._detected = True
            return True

        self._detected = False
        return False

    def get_language(self) -> str:
        """
        検出された言語名を返す

        Returns:
            言語名（例: 'python', 'javascript'）
        """
        return self.language

    def detect_package_manager(self) -> str | None:
        """
        使用されているパッケージマネージャを検出

        Returns:
            パッケージマネージャ名（例: 'pip', 'npm', 'yarn'）またはNone
        """
        # 言語ごとに特別な処理が必要な場合
        if self.language == "python":
            return DetectorPatterns.detect_python_package_manager(self.project_root)

        # 一般的な検出ロジック
        def file_exists_func(*patterns):
            """ファイル存在チェック関数"""
            if len(patterns) == 1:
                return (self.project_root / patterns[0]).exists()
            else:
                # 複数のファイルがすべて存在する場合
                return all((self.project_root / p).exists() for p in patterns)

        return DetectorPatterns.detect_package_manager(self.language, file_exists_func)

    def get_detected_language_object(self) -> DetectedLanguage:
        """
        検出された言語のオブジェクトを返す

        Returns:
            DetectedLanguage オブジェクト
        """
        pm = self.detect_package_manager()
        extensions = DetectorPatterns.get_source_extensions(self.language)
        return DetectedLanguage(
            name=self.language,
            package_manager=pm,
            source_extensions=extensions,
        )


class UnifiedDetectorFactory:
    """UnifiedDetector のファクトリークラス

    サポートされているすべての言語の detector を生成します。
    """

    @classmethod
    def get_all_languages(cls) -> list[str]:
        """
        サポートされているすべての言語を取得

        Returns:
            言語名のリスト（よく使われる言語を優先）
        """
        # パッケージファイルまたはソース拡張子が定義されている言語
        package_languages = set(DetectorPatterns.PACKAGE_FILES.keys())
        source_languages = set(DetectorPatterns.SOURCE_EXTENSIONS.keys())
        all_languages = sorted(package_languages | source_languages)

        # よく使われる言語を優先的にチェック（パッケージファイルチェックが高速なため）
        priority_languages = ["python", "javascript", "typescript", "go", "rust", "java"]
        ordered = []
        for lang in priority_languages:
            if lang in all_languages:
                ordered.append(lang)
        # 残りの言語を追加
        for lang in all_languages:
            if lang not in ordered:
                ordered.append(lang)

        return ordered

    @classmethod
    def create_detector(cls, project_root: Path, language: str) -> UnifiedDetector:
        """
        指定された言語の detector を作成

        Args:
            project_root: プロジェクトのルートディレクトリ
            language: 言語名

        Returns:
            UnifiedDetector インスタンス
        """
        return UnifiedDetector(project_root, language)

    @classmethod
    def create_all_detectors(cls, project_root: Path) -> list[UnifiedDetector]:
        """
        すべての言語の detector を作成

        Args:
            project_root: プロジェクトのルートディレクトリ

        Returns:
            UnifiedDetector インスタンスのリスト
        """
        return [cls.create_detector(project_root, lang) for lang in cls.get_all_languages()]
