"""ドキュメント検証モジュール

生成されたドキュメントの検証（出典チェック、幻覚検出）を行います。
"""

from pathlib import Path
import re
from typing import Any

from ..utils.logger import get_logger

logger = get_logger(__name__)


class DocumentValidator:
    """ドキュメント検証クラス"""

    # デフォルトの技術的な主張を示すキーワード（英語）
    DEFAULT_TECHNICAL_KEYWORDS = [
        "function",
        "class",
        "method",
        "module",
        "package",
        "import",
        "export",
        "implements",
        "extends",
        "returns",
        "parameter",
        "argument",
        "type",
        "defined",
        "located",
        "configured",
    ]

    # デフォルトの言語ごとのキーワード
    DEFAULT_LANGUAGE_KEYWORDS: dict[str, list[str]] = {
        "ja": ["関数", "クラス", "メソッド", "モジュール", "パッケージ", "実装", "定義"],
        "ko": ["함수", "클래스", "메서드", "모듈", "패키지", "구현", "정의"],
    }

    # 機密情報のパターン
    SECRET_PATTERNS = [
        r"[A-Za-z0-9_]{32,}",  # 長いランダム文字列
        r"sk-[A-Za-z0-9]{20,}",  # OpenAI APIキー
        r"ghp_[A-Za-z0-9]{36}",  # GitHub Personal Access Token
        r"AIza[A-Za-z0-9_-]{35}",  # Google APIキー
        r"AKIA[0-9A-Z]{16}",  # AWS Access Key
        r"[a-f0-9]{64}",  # SHA256ハッシュ (tokenの可能性)
    ]

    def __init__(self, project_root: Path | None = None, config: dict[str, Any] | None = None):
        """
        初期化

        Args:
            project_root: プロジェクトルート
            config: 設定辞書（技術キーワードの設定を含む）
        """
        self.project_root = project_root or Path.cwd()
        self.config = config or {}

        # 設定から技術キーワードを読み込む
        self.TECHNICAL_KEYWORDS = self._load_technical_keywords()

    def _load_technical_keywords(self) -> list[str]:
        """
        設定から技術キーワードを読み込む

        Returns:
            技術キーワードのリスト
        """
        keywords = []

        # デフォルトキーワードを取得
        keyword_config = self.config.get("validator", {}).get("technical_keywords", {})
        default_keywords = keyword_config.get("default", [])

        if default_keywords:
            keywords.extend(default_keywords)
        else:
            # 設定がない場合はデフォルト値を使用
            keywords.extend(self.DEFAULT_TECHNICAL_KEYWORDS)

        # 言語ごとのキーワードを追加
        language = self.config.get("general", {}).get("default_language", "en")
        language_keywords_config = keyword_config.get("languages", {})

        if language in language_keywords_config:
            keywords.extend(language_keywords_config[language])
        elif language in self.DEFAULT_LANGUAGE_KEYWORDS:
            # 設定がない場合はデフォルト値を使用
            keywords.extend(self.DEFAULT_LANGUAGE_KEYWORDS[language])

        return keywords

    def validate_citations(self, document: str, strict: bool = False) -> list[str]:
        """
        ドキュメント内の出典を検証

        Args:
            document: 検証対象のドキュメント
            strict: 厳格モード（技術的主張に出典がない場合もエラー）

        Returns:
            エラーメッセージのリスト
        """
        errors = []

        # [file:line] パターンを抽出
        citation_pattern = r"\[([^:\[\]]+):(\d+)(?:-(\d+))?\]"
        citations = re.findall(citation_pattern, document)

        logger.info(f"Found {len(citations)} citations in document")

        # 各出典の存在確認
        for file_path, start_line, end_line in citations:
            full_path = self.project_root / file_path

            if not full_path.exists():
                errors.append(f"❌ Referenced file not found: {file_path}")
                continue

            # ファイルは存在するので行番号の妥当性チェック
            try:
                content = full_path.read_text(encoding="utf-8")
                lines = content.splitlines()

                start = int(start_line)
                if start < 1 or start > len(lines):
                    errors.append(
                        f"❌ Invalid line number in {file_path}: "
                        f"line {start} (file has {len(lines)} lines)"
                    )

                if end_line:
                    end = int(end_line)
                    if end < start or end > len(lines):
                        errors.append(
                            f"❌ Invalid line range in {file_path}: "
                            f"lines {start}-{end} (file has {len(lines)} lines)"
                        )

            except (UnicodeDecodeError, PermissionError) as e:
                logger.warning(f"Could not read {file_path}: {e}")

        # 厳格モード: 技術的主張に出典がないかチェック
        if strict:
            missing_citations = self._find_missing_citations(document)
            errors.extend(missing_citations)

        return errors

    def _find_missing_citations(self, document: str) -> list[str]:
        """技術的主張に出典がない箇所を検出"""
        warnings = []

        # センテンス分割（簡易版）
        sentences = re.split(r"[。.](?:\s|$)", document)

        for sent in sentences:
            # 技術的キーワードを含むかチェック
            has_technical_keyword = any(
                keyword in sent.lower() for keyword in self.TECHNICAL_KEYWORDS
            )

            # 出典があるかチェック
            has_citation = re.search(r"\[.+:\d+\]", sent)

            if has_technical_keyword and not has_citation:
                # コメントやメタ情報は除外
                if not sent.strip().startswith(("#", "//", "<!--", ">", "-")):
                    warnings.append(f"⚠️  Missing citation in: {sent.strip()[:80]}...")

        return warnings

    def detect_secrets(self, document: str) -> list[str]:
        """
        ドキュメント内の機密情報を検出

        Args:
            document: 検証対象のドキュメント

        Returns:
            警告メッセージのリスト
        """
        warnings = []

        # コードブロックを抽出（機密情報は主にここに含まれる可能性）
        code_blocks = re.findall(r"```[^`]*```", document, re.DOTALL)

        for i, block in enumerate(code_blocks):
            for pattern in self.SECRET_PATTERNS:
                matches = re.findall(pattern, block)
                if matches:
                    warnings.append(
                        f"🔒 Potential secret detected in code block #{i + 1}: "
                        f"{pattern} matched {len(matches)} time(s)"
                    )

        # 本文中の機密情報パターン
        for pattern in self.SECRET_PATTERNS:
            matches = re.findall(pattern, document)
            if matches:
                # コードブロック内でなければ警告
                for match in matches:
                    if not any(match in block for block in code_blocks):
                        warnings.append(f"🔒 Potential secret in document body: {match[:20]}...")

        return warnings

    def validate(
        self,
        document: str,
        check_citations: bool = True,
        check_secrets: bool = True,
        strict: bool = False,
    ) -> dict[str, Any]:
        """
        ドキュメントの総合検証

        Args:
            document: 検証対象のドキュメント
            check_citations: 出典チェックを行うか
            check_secrets: 機密情報チェックを行うか
            strict: 厳格モード

        Returns:
            検証結果の辞書
        """
        result: dict[str, Any] = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }

        if check_citations:
            citation_errors = self.validate_citations(document, strict=strict)
            result["errors"].extend(citation_errors)  # type: ignore[attr-defined]

        if check_secrets:
            secret_warnings = self.detect_secrets(document)
            result["warnings"].extend(secret_warnings)  # type: ignore[attr-defined]

        # エラーがあれば無効
        if result["errors"]:
            result["valid"] = False

        # サマリーをログ出力
        logger.info(
            f"Validation complete: "
            f"{len(result['errors'])} errors, "
            f"{len(result['warnings'])} warnings"
        )

        return result

    def print_report(self, validation_result: dict[str, Any]):
        """検証結果をコンソールに出力"""
        print("\n" + "=" * 60)
        print("📋 Document Validation Report")
        print("=" * 60)

        if validation_result["valid"]:
            print("✅ Document is valid!")
        else:
            print("❌ Document has errors")

        if validation_result["errors"]:
            print(f"\n🚫 Errors ({len(validation_result['errors'])}):")
            for error in validation_result["errors"]:
                print(f"  {error}")

        if validation_result["warnings"]:
            print(f"\n⚠️  Warnings ({len(validation_result['warnings'])}):")
            for warning in validation_result["warnings"]:
                print(f"  {warning}")

        if not validation_result["errors"] and not validation_result["warnings"]:
            print("\n✨ No issues found!")

        print("=" * 60 + "\n")
