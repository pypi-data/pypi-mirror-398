"""
実装検証モジュール

ドキュメント内で言及されている関数、クラス、メソッドが
実際のコードベースに存在するかを検証します。
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..generators.parsers.base_parser import BaseParser
from ..generators.parsers.parser_factory import ParserFactory
from ..utils.logger import get_logger

if TYPE_CHECKING:
    from ..models import APIInfo

logger = get_logger("implementation_validator")


@dataclass
class EntityReference:
    """ドキュメント内で参照されているエンティティ"""

    name: str
    entity_type: str  # 'function', 'class', 'method'
    context: str  # 参照が見つかったコンテキスト（行の一部など）
    line_number: int | None = None
    file_path: str | None = None


@dataclass
class ValidationResult:
    """検証結果"""

    valid: bool
    errors: list[str]
    warnings: list[str]
    missing_entities: list[EntityReference]
    found_entities: list[EntityReference]


class ImplementationValidator:
    """実装検証クラス

    ドキュメント内で言及されている関数、クラス、メソッドが
    実際のコードベースに存在するかを検証します。
    """

    # 関数/メソッド名を抽出する正規表現パターン
    FUNCTION_PATTERNS = [
        # Python: def function_name, async def function_name
        r"\bdef\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
        r"\basync\s+def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
        # JavaScript/TypeScript: function functionName, const functionName =, functionName()
        r"\bfunction\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(",
        r"\bconst\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(?:async\s+)?\(",
        r"\b([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\([^)]*\)",  # 関数呼び出し
        # Go: func FunctionName
        r"\bfunc\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
        # Rust: fn function_name
        r"\bfn\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
        # Java/C++: returnType functionName(
        r"\b([a-zA-Z_][a-zA-Z0-9_<>[\]]*)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
    ]

    # クラス名を抽出する正規表現パターン
    CLASS_PATTERNS = [
        # Python: class ClassName
        r"\bclass\s+([a-zA-Z_][a-zA-Z0-9_]*)\b",
        # JavaScript/TypeScript: class ClassName
        r"\bclass\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\b",
        # Go: type TypeName struct
        r"\btype\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+struct\b",
        # Rust: struct StructName, impl StructName
        r"\bstruct\s+([a-zA-Z_][a-zA-Z0-9_]*)\b",
        r"\bimpl\s+([a-zA-Z_][a-zA-Z0-9_]*)\b",
        # Java/C++: class ClassName, public class ClassName
        r"\b(?:public\s+)?class\s+([a-zA-Z_][a-zA-Z0-9_]*)\b",
    ]

    def __init__(
        self,
        project_root: Path,
        languages: list[str] | None = None,
        parsers: list[BaseParser] | None = None,
        config: dict[str, Any] | None = None,
    ):
        """
        初期化

        Args:
            project_root: プロジェクトのルートディレクトリ
            languages: 検出された言語のリスト（Noneの場合は自動検出）
            parsers: パーサーのリスト（Noneの場合は自動生成）
            config: 設定辞書
        """
        self.project_root = project_root
        self.config = config or {}
        self.implemented_apis: dict[str, dict[str, Any]] = {}
        self._api_index: dict[str, set[str]] = {}  # {entity_type: {name1, name2, ...}}

        # パーサーの初期化
        if parsers is not None:
            self.parsers = parsers
        elif languages is not None:
            self.parsers = ParserFactory.create_parsers(project_root, languages)
        else:
            # 言語を自動検出
            from ..language_detector import LanguageDetector

            detector = LanguageDetector(project_root)
            detected_languages = detector.detect_languages()
            languages = [lang.name for lang in detected_languages]
            self.parsers = ParserFactory.create_parsers(project_root, languages)

        # 検証設定
        validation_config = self.config.get("validation", {})
        self.check_implementation = validation_config.get("check_implementation", True)
        self.warn_on_missing = validation_config.get("warn_on_missing", True)
        self.exclude_patterns = validation_config.get("implementation", {}).get(
            "exclude_patterns", ["test_", "_test", "mock_"]
        )
        self.include_private = validation_config.get("implementation", {}).get(
            "include_private", False
        )

    def build_api_index(self) -> dict[str, set[str]]:
        """
        実装済みAPIのインデックスを構築

        Returns:
            {entity_type: {name1, name2, ...}} の形式の辞書
        """
        if self._api_index:
            return self._api_index

        logger.info("実装済みAPIのインデックスを構築中...")

        # 除外ディレクトリの設定
        exclude_dirs = self.config.get("exclude", {}).get("directories", [])
        if not exclude_dirs:
            from ..detectors.detector_patterns import DetectorPatterns

            exclude_dirs = list(DetectorPatterns.EXCLUDE_DIRS) + ["venv"]

        # .gitignoreマッチャー
        gitignore_matcher = None
        use_gitignore = self.config.get("exclude", {}).get("use_gitignore", True)
        if use_gitignore:
            from ..utils.gitignore_parser import load_gitignore_patterns

            gitignore_matcher = load_gitignore_patterns(self.project_root)

        # 各パーサーでAPI情報を収集
        all_apis = []
        for parser in self.parsers:
            try:
                # ファイルスキャンは一度だけ行う（最初のパーサーで）
                files_to_parse = None
                if parser == self.parsers[0]:
                    # 最初のパーサーでファイルスキャン
                    files_to_parse = self._scan_project_files(
                        exclude_dirs, parser.get_supported_extensions(), gitignore_matcher
                    )

                apis = parser.parse_project(
                    exclude_dirs=exclude_dirs,
                    use_cache=True,
                    cache_manager=None,  # キャッシュは使用しない（検証用）
                    files_to_parse=files_to_parse,
                    skip_cache_save=True,
                    gitignore_matcher=gitignore_matcher,
                )
                all_apis.extend(apis)
            except (AttributeError, TypeError) as e:
                logger.debug(f"パーサー {parser.get_parser_type()} のAPI抽出でエラー: {e}")
            except Exception as e:
                logger.warning(f"パーサー {parser.get_parser_type()} で予期しないエラーが発生しました: {e}", exc_info=True)

        # インデックスを構築
        self._api_index = {"function": set(), "method": set(), "class": set()}
        self.implemented_apis = {}

        for api in all_apis:
            # APIInfoは辞書形式で使用される
            name = api.get("name") if isinstance(api, dict) else api.name
            entity_type = api.get("type") if isinstance(api, dict) else api.type

            # プライベートメソッドの除外
            if not self.include_private and name.startswith("_") and not name.startswith("__"):
                continue

            # 除外パターンのチェック
            if any(pattern in name for pattern in self.exclude_patterns):
                continue

            # インデックスに追加
            if entity_type in self._api_index:
                self._api_index[entity_type].add(name)

            # 詳細情報を保存
            key = f"{entity_type}:{name}"
            self.implemented_apis[key] = api.model_dump() if hasattr(api, "model_dump") else api  # type: ignore[assignment]

        logger.info(
            f"インデックス構築完了: "
            f"関数={len(self._api_index['function'])}, "
            f"メソッド={len(self._api_index['method'])}, "
            f"クラス={len(self._api_index['class'])}"
        )

        return self._api_index

    def _scan_project_files(
        self,
        exclude_dirs: list[str],
        extensions: list[str],
        gitignore_matcher: Any | None = None,
    ) -> list[tuple[Path, Path]]:
        """プロジェクトファイルをスキャン"""
        files_to_parse = []
        project_root_resolved = self.project_root.resolve()
        extensions_set = {ext.lower() for ext in extensions}

        try:
            import os

            for root, dirs, files in os.walk(self.project_root, followlinks=False):
                root_path = Path(root)

                # 除外ディレクトリの処理
                dirs_to_remove = []
                for d in dirs:
                    dir_path = root_path / d
                    if d in exclude_dirs or d.startswith(".") or d.endswith(".egg-info"):
                        dirs_to_remove.append(d)
                        continue
                    if gitignore_matcher and gitignore_matcher.should_exclude_dir(dir_path):
                        dirs_to_remove.append(d)
                        continue

                for d in dirs_to_remove:
                    dirs.remove(d)

                # パスベースの除外チェック
                try:
                    rel_path = root_path.relative_to(project_root_resolved)
                    if any(excluded in rel_path.parts for excluded in exclude_dirs):
                        dirs[:] = []
                        continue
                    if any(part.endswith(".egg-info") for part in rel_path.parts):
                        dirs[:] = []
                        continue
                    if gitignore_matcher and gitignore_matcher.should_exclude_dir(root_path):
                        dirs[:] = []
                        continue
                except ValueError:
                    continue

                # ファイルをチェック
                for file_name in files:
                    file_path = root_path / file_name

                    if gitignore_matcher and gitignore_matcher.is_ignored(file_path):
                        continue

                    ext = file_path.suffix.lower()
                    if ext not in extensions_set:
                        continue

                    try:
                        file_path_resolved = file_path.resolve()
                        try:
                            file_path_relative = file_path_resolved.relative_to(
                                project_root_resolved
                            )
                        except ValueError:
                            continue

                        if file_path.is_symlink():
                            continue

                        files_to_parse.append((file_path, file_path_relative))
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError) as e:
            logger.warning(f"プロジェクトの走査中にエラーが発生しました: {e}")

        return files_to_parse

    def extract_referenced_entities(self, document: str) -> list[EntityReference]:
        """
        ドキュメントから参照されているエンティティを抽出

        Args:
            document: 検証対象のドキュメント（Markdown形式）

        Returns:
            参照されているエンティティのリスト
        """
        entities = []

        # コードブロックを除外（実装コードなので検証対象外）
        code_blocks = []
        code_block_pattern = r"```[^`]*?```"
        for match in re.finditer(code_block_pattern, document, re.DOTALL):
            code_blocks.append((match.start(), match.end()))

        def is_in_code_block(pos: int) -> bool:
            """位置がコードブロック内かどうかを判定"""
            return any(start <= pos < end for start, end in code_blocks)

        lines = document.split("\n")
        for line_num, line in enumerate(lines, 1):
            line_start_pos = sum(len(l) + 1 for l in lines[: line_num - 1])

            # コードブロック内はスキップ
            if is_in_code_block(line_start_pos):
                continue

            # 関数/メソッド名を抽出
            for pattern in self.FUNCTION_PATTERNS:
                for match in re.finditer(pattern, line):
                    if is_in_code_block(line_start_pos + match.start()):
                        continue

                    name = match.group(1) if match.lastindex is not None and match.lastindex >= 1 else match.group(2)
                    if name:
                        # 一般的な単語を除外
                        if name.lower() in ["def", "async", "function", "const", "let", "var"]:
                            continue

                        entities.append(
                            EntityReference(
                                name=name,
                                entity_type="function",
                                context=line.strip()[:100],
                                line_number=line_num,
                            )
                        )

            # クラス名を抽出
            for pattern in self.CLASS_PATTERNS:
                for match in re.finditer(pattern, line):
                    if is_in_code_block(line_start_pos + match.start()):
                        continue

                    name = match.group(1) if match.lastindex is not None and match.lastindex >= 1 else match.group(2)
                    if name:
                        # 一般的な単語を除外
                        if name.lower() in ["class", "struct", "type", "impl"]:
                            continue

                        entities.append(
                            EntityReference(
                                name=name,
                                entity_type="class",
                                context=line.strip()[:100],
                                line_number=line_num,
                            )
                        )

        # 重複を除去（名前とタイプが同じもの）
        seen = set()
        unique_entities = []
        for entity in entities:
            key = (entity.name, entity.entity_type)
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)

        return unique_entities

    def validate_implementation(self, document: str) -> ValidationResult:
        """
        実装の存在を検証

        Args:
            document: 検証対象のドキュメント

        Returns:
            検証結果
        """
        if not self.check_implementation:
            return ValidationResult(
                valid=True, errors=[], warnings=[], missing_entities=[], found_entities=[]
            )

        # APIインデックスを構築
        api_index = self.build_api_index()

        # 参照されているエンティティを抽出
        referenced_entities = self.extract_referenced_entities(document)

        errors = []
        warnings = []
        missing_entities = []
        found_entities = []

        for entity in referenced_entities:
            # 実装されているかチェック
            entity_names = api_index.get(entity.entity_type, set())
            if entity.name in entity_names:
                found_entities.append(entity)
            else:
                # メソッドの場合は、クラス名.メソッド名の形式もチェック
                if entity.entity_type == "function" and "." in entity.name:
                    # クラス名.メソッド名の形式
                    parts = entity.name.split(".", 1)
                    if len(parts) == 2:
                        class_name, method_name = parts
                        if class_name in api_index.get("class", set()):
                            # クラスは存在するが、メソッドの存在は確認できない
                            # （メソッド名だけでは判断できないため、警告のみ）
                            if self.warn_on_missing:
                                warnings.append(
                                    f"⚠️  メソッド '{entity.name}' の実装を確認できませんでした "
                                    f"(行 {entity.line_number})"
                                )
                            found_entities.append(entity)
                            continue

                # 実装されていない
                missing_entities.append(entity)
                message = (
                    f"❌ 実装されていない {entity.entity_type} '{entity.name}' "
                    f"がドキュメントに記載されています (行 {entity.line_number})"
                )
                if self.warn_on_missing:
                    warnings.append(message)
                else:
                    errors.append(message)

        valid = len(errors) == 0

        logger.info(
            f"検証完了: 参照={len(referenced_entities)}, "
            f"実装済み={len(found_entities)}, "
            f"未実装={len(missing_entities)}"
        )

        return ValidationResult(
            valid=valid,
            errors=errors,
            warnings=warnings,
            missing_entities=missing_entities,
            found_entities=found_entities,
        )

    def get_implemented_api_summary(self) -> str:
        """
        実装済みAPIのサマリーを取得（LLMプロンプト用）

        Returns:
            実装済みAPIのサマリーテキスト
        """
        api_index = self.build_api_index()

        lines = ["実装済みAPI情報:"]
        lines.append("")

        # 関数
        if api_index.get("function"):
            lines.append("関数:")
            for name in sorted(api_index["function"])[:50]:  # 最大50件
                lines.append(f"  - {name}")
            if len(api_index["function"]) > 50:
                lines.append(f"  ... 他 {len(api_index['function']) - 50} 件")
            lines.append("")

        # クラス
        if api_index.get("class"):
            lines.append("クラス:")
            for name in sorted(api_index["class"])[:50]:  # 最大50件
                lines.append(f"  - {name}")
            if len(api_index["class"]) > 50:
                lines.append(f"  ... 他 {len(api_index['class']) - 50} 件")
            lines.append("")

        # メソッド
        if api_index.get("method"):
            lines.append("メソッド:")
            for name in sorted(api_index["method"])[:50]:  # 最大50件
                lines.append(f"  - {name}")
            if len(api_index["method"]) > 50:
                lines.append(f"  ... 他 {len(api_index['method']) - 50} 件")
            lines.append("")

        return "\n".join(lines)

    def print_report(self, validation_result: ValidationResult):
        """検証結果をコンソールに出力"""
        print("\n" + "=" * 60)
        print("📋 Implementation Validation Report")
        print("=" * 60)

        if validation_result.valid:
            print("✅ すべての参照が実装されています")
        else:
            print("❌ 実装されていない参照が見つかりました")

        if validation_result.errors:
            print(f"\n🚫 Errors ({len(validation_result.errors)}):")
            for error in validation_result.errors:
                print(f"  {error}")

        if validation_result.warnings:
            print(f"\n⚠️  Warnings ({len(validation_result.warnings)}):")
            for warning in validation_result.warnings:
                print(f"  {warning}")

        if validation_result.found_entities:
            print(f"\n✅ Found ({len(validation_result.found_entities)}):")
            for entity in validation_result.found_entities[:10]:  # 最初の10件のみ
                print(f"  - {entity.entity_type}: {entity.name}")

        if validation_result.missing_entities:
            print(f"\n❌ Missing ({len(validation_result.missing_entities)}):")
            for entity in validation_result.missing_entities[:10]:  # 最初の10件のみ
                print(f"  - {entity.entity_type}: {entity.name} (行 {entity.line_number})")

        print("=" * 60 + "\n")

