"""
パーサーファクトリーモジュール

言語に応じた適切なパーサーを生成するファクトリークラス。
言語とパーサーの対応を一元管理し、拡張性を向上させる。
"""

from pathlib import Path
from typing import TYPE_CHECKING

from .base_parser import BaseParser
from .generic_parser import GenericParser
from .js_parser import JSParser
from .python_parser import PythonParser

if TYPE_CHECKING:
    pass

__all__ = ["ParserFactory"]


class ParserFactory:
    """パーサーファクトリークラス

    言語名から適切なパーサーを選択して生成します。
    """

    # 言語とパーサークラスの対応マップ
    _PARSER_MAP: dict[str, type[BaseParser]] = {
        "python": PythonParser,
        "javascript": JSParser,
        "typescript": JSParser,  # TypeScriptもJSParserを使用
    }

    @classmethod
    def create_parser(cls, project_root: Path, language: str) -> BaseParser:
        """
        指定された言語のパーサーを作成

        Args:
            project_root: プロジェクトのルートディレクトリ
            language: 言語名（例: 'python', 'javascript', 'go'）

        Returns:
            パーサーインスタンス

        Raises:
            ValueError: サポートされていない言語が指定された場合
        """
        # 専用パーサーが定義されている場合
        parser_class = cls._PARSER_MAP.get(language)
        if parser_class:
            return parser_class(project_root)

        # GenericParserを使用（言語名を渡す）
        return GenericParser(project_root, language=language)

    @classmethod
    def create_parsers(cls, project_root: Path, languages: list[str]) -> list[BaseParser]:
        """
        複数の言語のパーサーを作成

        Args:
            project_root: プロジェクトのルートディレクトリ
            languages: 言語名のリスト

        Returns:
            パーサーインスタンスのリスト
        """
        parsers = []
        seen_parsers = set()  # 重複を避けるため（例: javascriptとtypescriptは同じパーサー）

        for lang in languages:
            # 同じパーサー型を複数作成しないようにチェック
            parser = cls.create_parser(project_root, lang)
            parser_type = type(parser).__name__

            if parser_type not in seen_parsers:
                parsers.append(parser)
                seen_parsers.add(parser_type)

        return parsers

    @classmethod
    def get_supported_languages(cls) -> list[str]:
        """
        サポートされている言語のリストを取得

        Returns:
            言語名のリスト
        """
        from ...detectors.detector_patterns import DetectorPatterns

        # DetectorPatternsから全言語を取得
        all_languages = set(DetectorPatterns.SOURCE_EXTENSIONS.keys())
        all_languages.update(DetectorPatterns.PACKAGE_FILES.keys())

        return sorted(all_languages)

    @classmethod
    def is_language_supported(cls, language: str) -> bool:
        """
        指定された言語がサポートされているかチェック

        Args:
            language: 言語名

        Returns:
            サポートされている場合True
        """
        from ...detectors.detector_patterns import DetectorPatterns

        return (
            language in cls._PARSER_MAP
            or language in DetectorPatterns.SOURCE_EXTENSIONS
            or language in DetectorPatterns.PACKAGE_FILES
        )
