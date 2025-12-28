"""
CONTRIBUTING.md generation module
"""

from typing import Any

from ..models.project import ProjectInfo
from ..utils.markdown_utils import get_current_timestamp
from .base_generator import BaseGenerator


class ContributingGenerator(BaseGenerator):
    """CONTRIBUTING.md generation class"""

    def _get_mode_key(self) -> str:
        return "contributing_mode"

    def _get_output_key(self) -> str:
        return "contributing"

    def _get_document_type(self) -> str:
        return "CONTRIBUTING.md"

    def _get_default_filename(self) -> str:
        return "CONTRIBUTING.md"

    def _convert_structured_data_to_markdown(
        self, structured_data: Any, project_info: ProjectInfo
    ) -> str:
        """構造化データをマークダウンに変換（現時点では未実装）"""
        return ""

    def _get_project_overview_section(self, content: str) -> str:
        """プロジェクト概要セクションを取得（現時点では未実装）"""
        return ""

    def _get_structured_model(self) -> Any:
        """構造化モデルを取得（現時点では未実装）"""
        return None

    def _create_llm_prompt(self, project_info: ProjectInfo, rag_context: str = "") -> str:
        """LLM用のプロンプトを作成（現時点では未実装）"""
        return ""

    def _generate_template(self, project_info: ProjectInfo) -> str:
        """
        Jinja2テンプレートを使用してCONTRIBUTING.mdを生成

        Args:
            project_info: Project info

        Returns:
            CONTRIBUTING content
        """
        # コンテキストの準備
        context = {
            "project_name": self.project_root.name,
            "has_python": "python" in self.languages,
            "has_javascript": "javascript" in self.languages or "typescript" in self.languages,
            "has_go": "go" in self.languages,
            "python_pm": self.package_managers.get("python", "pip"),
            "js_pm": self.package_managers.get("javascript", "npm"),
            "test_commands": project_info.test_commands or [],
            "coding_standards": project_info.coding_standards or {},
            "linter": project_info.coding_standards.get("linter")
            if project_info.coding_standards
            else None,
            "formatter": project_info.coding_standards.get("formatter")
            if project_info.coding_standards
            else None,
            "footer": self._generate_footer(),
        }

        # Jinja2テンプレートでレンダリング
        return self.template_service.render("contributing_template.md.j2", context)

    def _generate_footer(self) -> str:
        """フッターを生成"""
        return f"*このCONTRIBUTING.mdは自動生成されています。最終更新: {get_current_timestamp()}*"
