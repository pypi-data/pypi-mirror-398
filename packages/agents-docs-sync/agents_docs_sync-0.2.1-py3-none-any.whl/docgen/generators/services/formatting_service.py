"""
Formatting Service

テキストフォーマット、マークダウン処理サービス。
FormattingMixin + MarkdownMixin を統合。
"""

from docgen.utils.markdown_utils import (
    DESCRIPTION_END,
    DESCRIPTION_START,
    get_current_timestamp,
)


class FormattingService:
    """フォーマット・マークダウン処理サービス"""

    LANGUAGE_DISPLAY_NAMES = {
        "python": "Python",
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "go": "Go",
        "rust": "Rust",
        "java": "Java",
        "cpp": "C++",
        "c": "C",
        "ruby": "Ruby",
        "php": "PHP",
        "shell": "Shell",
        "bash": "Bash",
        "kotlin": "Kotlin",
        "swift": "Swift",
        "csharp": "C#",
    }

    def format_languages(self, languages: list[str]) -> str:
        """
        言語リストをフォーマット

        Args:
            languages: 言語のリスト

        Returns:
            フォーマットされた言語リスト
        """
        if not languages:
            return "- Not detected"

        parts = []
        for lang in languages:
            display_name = self.LANGUAGE_DISPLAY_NAMES.get(lang, lang.capitalize())
            parts.append(f"- {display_name}")
        return "\n".join(parts)

    def format_commands(self, commands: list[str] | None) -> str:
        """
        コマンドリストをフォーマット

        Args:
            commands: コマンドのリスト

        Returns:
            フォーマットされたコマンド
        """
        if not commands:
            return ""
        return "\n".join([f"```bash\n{cmd}\n```" for cmd in commands])

    def format_project_structure(self, structure: dict | None) -> str:
        """
        プロジェクト構造をツリー形式でフォーマット

        Args:
            structure: プロジェクト構造の辞書

        Returns:
            フォーマットされたプロジェクト構造
        """
        if not structure:
            return ""

        lines: list[str] = []
        self._format_structure_tree(structure, lines, prefix="", is_last=True)
        return "\n".join(lines)

    def _format_structure_tree(
        self,
        structure: dict | list,
        lines: list[str],
        prefix: str = "",
        is_last: bool = True,
    ) -> None:
        """ツリー形式で構造を再帰的にフォーマット"""
        if isinstance(structure, dict):
            items = list(structure.items())
            for idx, (key, value) in enumerate(items):
                is_last_item = idx == len(items) - 1
                connector = "└── " if is_last_item else "├── "
                clean_key = key.rstrip("/") if key.endswith("//") else key

                if isinstance(value, dict):
                    lines.append(f"{prefix}{connector}{clean_key}/")
                    extension = "    " if is_last_item else "│   "
                    self._format_structure_tree(value, lines, prefix + extension, is_last_item)
                else:
                    lines.append(f"{prefix}{connector}{clean_key}")
        elif isinstance(structure, list):
            for idx, item in enumerate(structure):
                is_last_item = idx == len(structure) - 1
                connector = "└── " if is_last_item else "├── "
                clean_item = item.rstrip("/") if item.endswith("//") else item
                lines.append(f"{prefix}{connector}{clean_item}")

    def clean_llm_output(self, content: str) -> str:
        """
        LLMの出力をクリーニング

        Args:
            content: LLM出力

        Returns:
            クリーニングされたコンテンツ
        """
        if content.startswith("```markdown"):
            content = content.replace("```markdown", "", 1)
        elif content.startswith("```"):
            content = content.replace("```", "", 1)

        if content.endswith("```"):
            content = content[:-3]

        return content.strip()

    def validate_output(self, content: str) -> bool:
        """
        生成されたコンテンツを検証

        Args:
            content: 生成されたコンテンツ

        Returns:
            検証に成功した場合True
        """
        if not content:
            return False
        if len(content) < 50:
            return False
        return True

    def generate_footer(self, document_type: str) -> str:
        """
        フッターを生成

        Args:
            document_type: ドキュメントタイプ

        Returns:
            フッター文字列
        """
        return f"*この{document_type}は自動生成されています。最終更新: {get_current_timestamp()}*"

    def extract_description_section(self, content: str) -> str:
        """
        コンテンツから説明セクションを抽出

        Args:
            content: ドキュメントコンテンツ

        Returns:
            説明セクションのテキスト
        """
        lines = content.split("\n")
        description_lines = []
        in_description = False

        for line in lines:
            if DESCRIPTION_START in line:
                in_description = True
                continue
            elif DESCRIPTION_END in line:
                break
            elif in_description:
                description_lines.append(line)

        return "\n".join(description_lines)
