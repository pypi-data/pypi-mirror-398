"""
Template Service

Jinja2テンプレートのレンダリングサービス。
MixinパターンからDIへの移行に対応。
"""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader


class TemplateService:
    """テンプレートレンダリングサービス"""

    def __init__(self, template_dir: Path | None = None):
        """
        初期化

        Args:
            template_dir: テンプレートディレクトリのパス（Noneの場合は自動検出）
        """
        self._template_dir = template_dir or self._get_default_template_dir()
        self._env: Environment | None = None

    def _get_default_template_dir(self) -> Path:
        """デフォルトのテンプレートディレクトリを取得"""
        # docgen/generators/services/template_service.py -> docgen/templates
        current_dir = Path(__file__).parent
        template_dir = current_dir.parent.parent / "templates"

        if not template_dir.exists():
            # パッケージとしてインストールされている場合のフォールバック
            import docgen

            template_dir = Path(docgen.__file__).parent / "templates"

        return template_dir

    def _get_env(self) -> Environment:
        """Jinja2環境を取得（遅延初期化）"""
        if self._env is None:
            self._env = Environment(loader=FileSystemLoader(str(self._template_dir)))
        return self._env

    def render(self, template_name: str, context: dict[str, Any]) -> str:
        """
        テンプレートをレンダリング

        Args:
            template_name: テンプレートファイル名
            context: テンプレート変数

        Returns:
            レンダリングされた文字列
        """
        env = self._get_env()
        template = env.get_template(template_name)
        return template.render(context)

    def format_commands(self, commands: list[str]) -> str:
        """
        コマンドリストをマークダウンのコードブロックとしてフォーマット

        Args:
            commands: コマンドのリスト

        Returns:
            フォーマットされたマークダウン文字列
        """
        if not commands:
            return ""
        parts = ["```bash"]
        for cmd in commands[:5]:  # 最大5個
            parts.append(cmd)
        if len(commands) > 5:
            parts.append("# ... その他のコマンド")
        parts.append("```")
        return "\n".join(parts)

    def format_custom_instructions(self, custom_instructions: str | dict[str, Any]) -> list[str]:
        """
        カスタム指示セクションを生成

        Args:
            custom_instructions: カスタム指示の内容（文字列または辞書）

        Returns:
            生成された行のリスト
        """
        lines = []
        lines.append("## プロジェクト固有の指示")
        lines.append("")

        if isinstance(custom_instructions, str):
            lines.append(custom_instructions)
        elif isinstance(custom_instructions, dict):
            for key, value in custom_instructions.items():
                lines.append(f"### {key}")
                lines.append("")
                lines.append(str(value))
                lines.append("")

        lines.append("")
        return lines
