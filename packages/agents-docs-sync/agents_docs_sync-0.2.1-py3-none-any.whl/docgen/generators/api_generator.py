"""
APIドキュメント生成モジュール
"""

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..detectors.detector_patterns import DetectorPatterns
from ..models.api import APIInfo
from ..models.project import ProjectInfo
from ..utils.cache import CacheManager
from ..utils.markdown_utils import (
    GENERATION_TIMESTAMP_LABEL,
    SECTION_SEPARATOR,
    get_current_timestamp,
)
from .base_generator import BaseGenerator
from .parsers.parser_factory import ParserFactory

if TYPE_CHECKING:
    from .parsers.base_parser import BaseParser


class APIGenerator(BaseGenerator):
    """APIドキュメント生成クラス"""

    def __init__(
        self,
        project_root: Path,
        languages: list[str],
        config: dict[str, Any],
        package_managers: dict[str, str] | None = None,
    ):
        """
        初期化

        Args:
            project_root: プロジェクトのルートディレクトリ
            languages: 検出された言語のリスト
            config: 設定辞書
            package_managers: 検出されたパッケージマネージャの辞書
        """
        super().__init__(project_root, languages, config, package_managers)

        # キャッシュマネージャーの初期化
        cache_enabled = self.config.get("cache", {}).get("enabled", True)
        self.cache_manager = (
            CacheManager(project_root=self.project_root, enabled=cache_enabled)
            if cache_enabled
            else None
        )

    def _get_mode_key(self) -> str:
        return "api_mode"

    def _get_output_key(self) -> str:
        return "api_doc"

    def _get_document_type(self) -> str:
        return "APIドキュメント"

    def _get_structured_model(self) -> Any:
        # 現在は構造化出力を使用していないためNoneを返す
        return None

    def _create_llm_prompt(self, project_info: ProjectInfo, rag_context: str = "") -> str:
        # 現在はLLM生成を使用していないため空文字を返す
        return ""

    def _generate_template(self, project_info: ProjectInfo) -> str:
        # テンプレート生成の代わりにパーサーベースの生成を行う
        # BaseGeneratorのgenerateフローから呼ばれる場合、ここが実質的な生成ロジックの一部になる
        # ただし、API生成は特殊なので、_generate_markdownで処理する
        return ""

    def _get_project_overview_section(self, content: str) -> str:
        return ""

    def _convert_structured_data_to_markdown(
        self, structured_data: Any, project_info: ProjectInfo
    ) -> str:
        return ""

    def _generate_markdown(self, project_info: ProjectInfo) -> str:
        """
        API情報からマークダウンを生成

        Args:
            project_info: プロジェクト情報（このクラスでは主に使用しないが、インターフェースとして必要）

        Returns:
            マークダウンの文字列
        """
        # 各言語のパーサーでAPI情報を収集
        all_apis = []
        parsers = self._get_parsers()

        # 除外ディレクトリとファイルパターンを設定
        exclude_dirs = self.config.get("exclude", {}).get(
            "directories",
            list(DetectorPatterns.EXCLUDE_DIRS) + ["venv"],
        )

        # キャッシュの使用設定
        use_cache = self.config.get("cache", {}).get("enabled", True)

        # .gitignoreマッチャーを作成
        gitignore_matcher = None
        use_gitignore = self.config.get("exclude", {}).get("use_gitignore", True)
        if use_gitignore:
            from ..utils.gitignore_parser import load_gitignore_patterns

            gitignore_matcher = load_gitignore_patterns(self.project_root)

        # 一度だけファイルスキャンを行い、結果を各パーサーに共有（重複スキャンを避ける）
        # すべてのパーサーの拡張子を集めて一度だけスキャン
        all_extensions = set()
        for parser in parsers:
            all_extensions.update(parser.get_supported_extensions())

        shared_files_to_parse = self._scan_project_files(
            exclude_dirs=exclude_dirs,
            extensions=all_extensions,
        )

        # 各パーサーで解析（ファイルスキャン結果を共有）
        parser_stats = {}  # パーサーごとの統計情報

        for i, parser in enumerate(parsers):
            parser_type = parser.get_parser_type()
            parser_language = getattr(parser, "language", parser_type)

            # 最後のパーサー以外はキャッシュ保存をスキップ（最後に一度だけ保存）
            skip_cache_save = i < len(parsers) - 1

            try:
                self.logger.info(
                    f"[API生成] {parser_language} ({parser_type}) パーサーで解析を開始..."
                )
                apis = parser.parse_project(
                    exclude_dirs=exclude_dirs,
                    use_cache=use_cache,
                    cache_manager=self.cache_manager,
                    files_to_parse=shared_files_to_parse,
                    skip_cache_save=skip_cache_save,
                    gitignore_matcher=gitignore_matcher,
                )
                all_apis.extend(apis)
                parser_stats[parser_language] = {
                    "type": parser_type,
                    "api_count": len(apis),
                    "status": "success",
                }
                self.logger.info(
                    f"[API生成] {parser_language} ({parser_type}): {len(apis)}件のAPI要素を抽出しました"
                )
            except (ImportError, AttributeError) as e:
                self.logger.error(
                    f"[API生成] {parser_language} ({parser_type}) パーサーの読み込みに失敗しました: {e}",
                    exc_info=True,
                )
            except Exception as e:
                self.logger.error(
                    f"[API生成] {parser_language} ({parser_type}) パーサーで予期しないエラーが発生しました: {e}",
                    exc_info=True,
                )
                parser_stats[parser_language] = {
                    "type": parser_type,
                    "api_count": 0,
                    "status": "error",
                    "error": str(e),
                }

        # すべてのパーサー実行後に一度だけキャッシュを保存
        if use_cache and self.cache_manager:
            self.cache_manager.save()

        # API情報をソート（ファイル名、行番号順）
        all_apis.sort(key=lambda x: (x.file_path, x.line_number or 0))

        return self._render_api_markdown(all_apis)

    def _render_api_markdown(self, apis: list[APIInfo]) -> str:
        """
        API情報のリストからマークダウンをレンダリング

        Args:
            apis: API情報のリスト

        Returns:
            マークダウン文字列
        """
        lines = []

        # ヘッダー
        lines.append("# API ドキュメント")
        lines.append("")
        lines.append(f"{GENERATION_TIMESTAMP_LABEL} {get_current_timestamp()}")
        lines.append("")
        lines.append(SECTION_SEPARATOR)
        lines.append("")

        if not apis:
            lines.append("APIが見つかりませんでした。")
            return "\n".join(lines)

        # ファイルごとにグループ化
        current_file = None
        for api in apis:
            file_path = api.file_path

            # 新しいファイルセクション
            if file_path != current_file:
                if current_file is not None:
                    lines.append("")
                current_file = file_path
                lines.append(f"## {file_path}")
                lines.append("")

            # API情報を出力
            lines.append(f"### {api.name}")
            lines.append("")
            lines.append(f"**型**: `{api.type}`")
            lines.append("")
            lines.append("**シグネチャ**:")
            lines.append("```")
            signature = api.signature or ""
            lines.append(signature)
            lines.append("```")
            lines.append("")

            if api.docstring:
                lines.append("**説明**:")
                lines.append("")
                # docstringを整形（インデントを調整）
                docstring_lines = api.docstring.split("\n")
                for doc_line in docstring_lines:
                    lines.append(doc_line)
                lines.append("")
            else:
                lines.append("*説明なし*")
                lines.append("")

            line_number = api.line_number or 0
            lines.append(f"*定義場所: {file_path}:{line_number}*")
            lines.append("")
            lines.append(SECTION_SEPARATOR)
            lines.append("")

        return "\n".join(lines)

    def _get_parsers(self) -> list["BaseParser"]:
        """
        言語に応じたパーサーのリストを取得
        パーサーファクトリーを使用してパーサーを生成

        Returns:
            パーサーのリスト
        """
        return ParserFactory.create_parsers(self.project_root, self.languages)

    def _scan_project_files(
        self, exclude_dirs: list[str], extensions: set[str]
    ) -> list[tuple[Path, Path]]:
        """
        プロジェクトファイルを一度だけスキャン（UnifiedFileScannerを使用）

        Args:
            exclude_dirs: 除外するディレクトリ
            extensions: スキャン対象の拡張子セット

        Returns:
            (絶対パス, 相対パス)のタプルのリスト
        """
        from ..utils.file_scanner import get_unified_scanner

        project_root_resolved = self.project_root.resolve()
        extensions_set = {ext.lower() for ext in extensions}

        # 統一ファイルスキャナーを取得
        use_gitignore = self.config.get("exclude", {}).get("use_gitignore", True)
        scanner = get_unified_scanner(
            project_root=self.project_root,
            exclude_dirs=set(exclude_dirs),
            use_gitignore=use_gitignore,
        )

        # スキャン結果を取得
        scan_result = scanner.scan_once()
        files_to_parse = []

        # 拡張子でフィルタリング
        try:
            for ext, files in scan_result["files_by_extension"].items():
                if ext.lower() in extensions_set:
                    for file_path in files:
                        try:
                            # パスの正規化（シンボリックリンクを解決）
                            file_path_resolved = file_path.resolve()

                            # プロジェクトルート外へのアクセスを防止
                            try:
                                file_path_relative = file_path_resolved.relative_to(
                                    project_root_resolved
                                )
                            except ValueError:
                                # プロジェクトルート外のファイルはスキップ
                                continue

                            # シンボリックリンクのチェック
                            if file_path.is_symlink():
                                continue

                            files_to_parse.append((file_path, file_path_relative))
                        except (OSError, PermissionError):
                            # ファイルアクセスエラーは無視して続行
                            continue
        except (OSError, PermissionError) as e:
            from ..utils.logger import get_logger

            logger = get_logger("api_generator")
            logger.warning(f"プロジェクトの走査中にエラーが発生しました: {e}")

        return files_to_parse
