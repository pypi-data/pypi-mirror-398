"""
README generation module
Achieve structured output with Outlines integration
"""

from pathlib import Path
from typing import Any

from ..models.project import ProjectInfo
from ..models.readme import ReadmeDocument
from ..utils.exceptions import GenerationError, LLMError
from ..utils.markdown_utils import DESCRIPTION_START, get_current_timestamp
from ..utils.prompt_loader import PromptLoader
from .base_generator import BaseGenerator


class ReadmeGenerator(BaseGenerator):
    """README generation class"""

    def __init__(
        self,
        project_root: Path,
        languages: list[str],
        config: dict[str, Any],
        package_managers: dict[str, str] | None = None,
        **kwargs: Any,
    ):
        """
        Initialize

        Args:
            project_root: Project root directory
            languages: List of detected languages
            config: Configuration dictionary
            package_managers: Dictionary of detected package managers
            **kwargs: Additional arguments passed to BaseGenerator (services, etc.)
        """
        super().__init__(project_root, languages, config, package_managers, **kwargs)
        self.preserve_manual = config.get("generation", {}).get("preserve_manual_sections", True)

    def _should_use_llm(self) -> bool:
        """README generation uses LLM based on mode setting"""
        generation_config = self.agents_config.get("generation", {})
        mode = generation_config.get(self._get_mode_key(), "template")
        return mode in ["llm", "hybrid"]

    @property
    def readme_path(self):
        return self.output_path

    def _get_mode_key(self) -> str:
        return "readme_mode"

    def _convert_structured_data_to_markdown(
        self, data: ReadmeDocument, project_info: ProjectInfo
    ) -> str:
        """
        構造化データをマークダウン形式に変換（テンプレート使用）

        Args:
            data: 構造化されたREADMEドキュメントデータ
            project_info: プロジェクト情報

        Returns:
            マークダウン形式の文字列
        """
        # 構造化データをテンプレートコンテキストに変換
        context = {
            "project_name": data.title,
            "description_section": data.description,
            "technologies": self._format_technologies(data.technologies),
            "dependencies_section": self._format_dependencies_from_data(data.dependencies),
            "setup_section": self._format_setup_instructions(data.setup_instructions),
            "usage_section": "",  # 使用方法は手動セクションまたは別途生成
            "build_commands": self.template_service.format_commands(data.build_commands or []),
            "test_commands": self.template_service.format_commands(data.test_commands or []),
            "other_section": "",
            "footer": f"*このREADME.mdは自動生成されています。最終更新: {get_current_timestamp()}*",
            "project_structure": data.project_structure
            or self.formatting_service.format_project_structure(project_info.project_structure),
            "key_features": data.key_features or self._generate_key_features(project_info),
            "architecture": data.architecture or self._generate_architecture(project_info),
            "troubleshooting": data.troubleshooting or self._generate_troubleshooting(project_info),
        }

        # 手動セクションの統合
        if data.manual_sections:
            if "usage" in data.manual_sections:
                context["usage_section"] = data.manual_sections["usage"]
            if "other" in data.manual_sections:
                context["other_section"] = data.manual_sections["other"]

        # テンプレートをレンダリングして文字列を返す
        return self.template_service.render("readme", context)

    def _format_technologies(self, technologies: list[str]) -> str:
        """使用技術リストを整形"""
        if not technologies:
            return ""
        return "\n".join([f"- {tech}" for tech in technologies])

    def _format_dependencies_from_data(self, dependencies: Any) -> str:
        """構造化データから依存関係を整形"""
        if not dependencies:
            return ""

        lines = []
        # ignored言語の依存関係は表示しない
        if dependencies.python and "python" in self.languages:
            lines.append("### Python")
            lines.extend([f"- {dep}" for dep in dependencies.python])
        if dependencies.nodejs and (
            "javascript" in self.languages or "typescript" in self.languages
        ):
            lines.append("### Node.js")
            lines.extend([f"- {dep}" for dep in dependencies.nodejs])
        if dependencies.other:
            lines.append("### Other")
            lines.extend([f"- {dep}" for dep in dependencies.other])

        return "\n".join(lines)

    def _format_setup_instructions(self, setup: Any) -> str:
        """セットアップ手順を整形"""
        if not setup:
            return ""

        lines = []
        if setup.prerequisites:
            lines.append("### 前提条件")
            lines.extend([f"- {req}" for req in setup.prerequisites])

        if setup.installation_steps:
            lines.append("### インストール")
            for step in setup.installation_steps:
                lines.append(f"1. {step}")

        return "\n".join(lines)

    def _get_default_prompt_file(self) -> str:
        """デフォルトのプロンプトファイル名を取得"""
        return "readme_prompts.toml"

    def _generate_markdown(self, project_info: ProjectInfo) -> str:
        """
        README用のマークダウンを生成（モード設定を正しく取得）
        """
        # generation設定を取得（agents_configから）
        generation_config = self.agents_config.get("generation", {})
        mode = generation_config.get(self._get_mode_key(), "template")

        if mode == "llm":
            # LLM完全生成
            return self._generate_with_llm(project_info)
        elif mode == "hybrid":
            # ハイブリッド生成
            return self._generate_hybrid(project_info)
        else:
            # テンプレート生成（デフォルト）
            return self._generate_template(project_info)

    def _get_output_key(self) -> str:
        return "readme"

    def _get_document_type(self) -> str:
        return "README.md"

    def _get_structured_model(self):
        return ReadmeDocument

    def _create_llm_prompt(self, project_info: ProjectInfo, rag_context: str = "") -> str:
        return self._create_readme_prompt(project_info, rag_context)

    def _create_readme_prompt(self, project_info: ProjectInfo, rag_context: str = "") -> str:
        """README生成用のLLMプロンプトを作成"""
        if rag_context:
            return PromptLoader.load_prompt(
                "readme_prompts.toml",
                "full_with_rag",
                config=self.config,
                project_info=self._format_project_info_for_prompt(project_info),
                rag_context=rag_context,
            )
        else:
            return PromptLoader.load_prompt(
                "readme_prompts.toml",
                "full",
                config=self.config,
                project_info=self._format_project_info_for_prompt(project_info),
            )

    def _convert_structured_data_to_markdown_legacy(self, data, project_info: ProjectInfo) -> str:
        """READMEの構造化データをマークダウン形式に変換（未使用・レガシー）"""
        # LLM生成では直接マークダウンを生成するため、このメソッドは使用しない
        return ""

    def _get_project_overview_section(self, content: str | None) -> str:
        """プロジェクト概要セクションを取得"""
        if content and DESCRIPTION_START in content:
            return self.formatting_service.extract_description_section(content)
        return content or ""

    def _collect_project_description(self) -> str:
        """プロジェクト説明を収集"""
        from ..utils.markdown_utils import extract_project_description

        return extract_project_description(
            self.project_root, "", self.readme_path, config=self.config
        )

    def _generate_setup_from_project_info(self, project_info: ProjectInfo) -> str:
        """プロジェクト情報からセットアップセクションを生成"""
        # セットアップ用のコンテキストを作成
        # package_managersが空の場合は自動検出
        if not self.package_managers:
            from ..language_detector import LanguageDetector

            detector = LanguageDetector(self.project_root)
            detector.detect_languages()
            self.package_managers = detector.get_detected_package_managers()

        setup_context = {
            "has_python": "python" in self.languages,
            "has_javascript": "javascript" in self.languages or "typescript" in self.languages,
            "has_go": "go" in self.languages,
            "python_pm": self.package_managers.get("python", "pip"),
            "js_pm": self.package_managers.get("javascript", "npm"),
        }

        # セットアップ用のサブテンプレートをレンダリング
        return self.template_service.render("setup_template.md.j2", setup_context)

    def _format_dependencies_from_languages(self) -> str:
        """検出された言語から依存関係セクションを生成（簡略化版）"""
        parts = []
        if "python" in self.languages:
            parts.append("- **Python**: `pyproject.toml` または `requirements.txt` を参照")
        if "javascript" in self.languages or "typescript" in self.languages:
            parts.append("- **Node.js**: `package.json` を参照")
        if "go" in self.languages:
            parts.append("- **Go**: `go.mod` を参照")

        return "\n".join(parts) if parts else "依存関係は検出されませんでした。"

    # _format_commandsはbase_generatorに移動したため削除

    def _format_manual_sections_for_prompt(self, manual_sections: dict[str, str]) -> str:
        """
        Format manual sections for prompt

        Args:
            manual_sections: Manual sections

        Returns:
            Formatted string
        """
        if not manual_sections:
            return "なし"

        lines = []
        for name, content in manual_sections.items():
            lines.append(f"{name}: {content[:200]}...")  # First 200 characters

        return "\n".join(lines)

    def _generate_template(self, project_info: ProjectInfo) -> str:
        """
        Jinja2テンプレートを使用してREADMEを生成

        Args:
            project_info: Project info

        Returns:
            README content
        """
        # Extract manual sections from existing README
        try:
            existing_content = self.readme_path.read_text()
            manual_sections = self.manual_section_service.extract(existing_content)
        except (FileNotFoundError, OSError):
            manual_sections = {}

        # コンテキストの準備
        context = {
            "project_name": self.project_root.name or "agents-docs-sync",
            "notice_section": "",  # 手動セクションは自動マージされるため、ここでは空にする（重複防止）
            "description_section": self._get_project_overview_section(project_info.description),
            "technologies": self.formatting_service.format_languages(self.languages),
            "dependencies_section": self._format_dependencies_from_languages(),
            "setup_section": manual_sections.get("setup", "").strip()
            or self._generate_setup_from_project_info(project_info),
            "usage_section": manual_sections.get("usage", ""),
            "build_commands": self.template_service.format_commands(project_info.build_commands),
            "test_commands": self.template_service.format_commands(project_info.test_commands),
            "other_section": "" if manual_sections.get("other") else "",
            "footer": self.formatting_service.generate_footer("README.md"),
            "project_structure": self.formatting_service.format_project_structure(
                project_info.project_structure
            ),
            # テンプレートモードではLLMを使用せず、データから取得した値のみ使用
            "key_features": project_info.key_features or [],
            "architecture": ""
            if manual_sections.get("architecture")
            else self._generate_architecture(project_info),
            "troubleshooting": "",
            "scripts": project_info.scripts,
        }

        # Jinja2テンプレートでレンダリング
        return self.template_service.render("readme_template.md.j2", context)

    def _create_overview_prompt(
        self, project_info: ProjectInfo, existing_overview: str, rag_context: str = ""
    ) -> str:
        """README生成用のLLMプロンプトを作成（BaseGeneratorのオーバーライド）"""
        return PromptLoader.load_prompt(
            "readme_prompts.toml",
            "overview",
            config=self.config,
            project_info=self._format_project_info_for_prompt(project_info),
            existing_overview=existing_overview,
            rag_context=rag_context,
        )

    def _replace_overview_section(self, content: str, new_overview: str) -> str:
        """
        プロジェクト概要セクションを置き換え（BaseGeneratorのオーバーライド）
        READMEではdescriptionセクションを置き換える
        """
        import re

        # パターン1: 手動セクションマーカーがある場合 (中身が空または空白のみ)
        # MANUAL_START:description ... MANUAL_END:description の後から、次のセクション（## 使用技術 または MANUAL_START:architecture）の前まで
        pattern_with_markers = r"(<!-- MANUAL_START:description -->\s*<!-- MANUAL_END:description -->\s*)(.*?)(\s*(?:## 使用技術|<!-- MANUAL_START:architecture -->))"

        if re.search(pattern_with_markers, content, flags=re.DOTALL):
            replacement = r"\1" + new_overview + r"\3"
            updated_content = re.sub(pattern_with_markers, replacement, content, flags=re.DOTALL)
        else:
            # パターン2: マーカーがない場合（テンプレート変更後）、タイトルと「使用技術」の間を置換
            # タイトル行（# ...）の次の行から ## 使用技術 の前まで
            pattern_no_markers = r"(# .*?\n)(.*?)(\n## 使用技術)"
            replacement = r"\1\n" + new_overview + r"\3"
            updated_content = re.sub(pattern_no_markers, replacement, content, flags=re.DOTALL)

        # デバッグ: 置換が成功したか確認
        if updated_content == content:
            self.logger.warning(
                "Overview section replacement did not match. Pattern may need adjustment."
            )
        else:
            self.logger.debug("Overview section successfully replaced.")

        return updated_content

    def _generate_description_section(self, manual_sections: dict[str, str]) -> str:
        """説明セクションの内容を生成"""
        if "description" in manual_sections:
            return manual_sections["description"]
        else:
            description = self._collect_project_description()
            if description:
                return description
            else:
                return "Please describe this project here."

    def _format_project_info_for_prompt(self, project_info: ProjectInfo) -> str:
        """プロジェクト情報をプロンプト用に整形"""
        base_info = self.llm_service.format_project_info(
            project_info, self.languages, self.package_managers
        )
        return f"Project Name: {self.project_root.name}\n{base_info}"

    def _generate_content_with_llm(
        self, prompt_file: str, prompt_name: str, project_info: ProjectInfo
    ) -> str:
        """LLMを使用してコンテンツを生成"""
        project_info_str = self._format_project_info_for_prompt(project_info)

        # RAGコンテキスト取得（改善されたクエリを使用）
        rag_context = ""
        if self.config.get("rag", {}).get("enabled", False):
            query = f"{prompt_name} for {self.project_root.name}"
            # プロジェクト情報を辞書形式で準備（説明を含める）
            project_info_dict = {
                "description": project_info.description,
                "key_features": project_info.key_features,
                "dependencies": project_info.dependencies,
            }
            rag_context = self.rag_service.get_context(
                query,
                use_enhanced_query=True,
                project_name=self.project_root.name,
                languages=self.languages,
                project_info=project_info_dict,
            )

        content = self.llm_service.generate_content(
            prompt_file, prompt_name, project_info_str, rag_context
        )
        return self.formatting_service.clean_llm_output(content)

    # LLMMixinのメソッドをここで再実装（サービス委譲）
    def _generate_with_llm(self, project_info: ProjectInfo) -> str:
        try:
            # Outlinesを使用するかどうか
            if self.llm_service.should_use_outlines():
                client = self.llm_service.get_client()
                if client:
                    outlines_model = self.llm_service.create_outlines_model(client)
                    if outlines_model:
                        # RAGコンテキスト（改善されたクエリを使用）
                        rag_context = ""
                        if self.config.get("rag", {}).get("enabled", False):
                            query = f"full documentation context for {self.project_root.name}"
                            project_info_dict = {
                                "description": project_info.description,
                                "key_features": project_info.key_features,
                                "dependencies": project_info.dependencies,
                            }
                            rag_context = self.rag_service.get_context(
                                query,
                                use_enhanced_query=True,
                                project_name=self.project_root.name,
                                languages=self.languages,
                                project_info=project_info_dict,
                            )

                        # プロンプト作成
                        prompt = self._create_llm_prompt(project_info, rag_context=rag_context)

                        # 生成
                        self.logger.info("Outlinesを使用して構造化されたドキュメントを生成中...")
                        structured_data = outlines_model(prompt, self._get_structured_model())

                        # 変換
                        return self._convert_structured_data_to_markdown(
                            structured_data, project_info
                        )

            # フォールバック: テンプレート生成
            self.logger.warning(
                "Outlinesが利用できないため、テンプレート生成にフォールバックします"
            )
            return self._generate_template(project_info)

        except (LLMError, GenerationError) as e:
            self.logger.error(f"LLM生成エラー: {e}")
            return self._generate_template(project_info)
        except Exception as e:
            self.logger.error(f"LLM生成中に予期しないエラーが発生しました: {e}", exc_info=True)
            return self._generate_template(project_info)

    def _generate_hybrid(self, project_info: ProjectInfo) -> str:
        # まずテンプレートでベースを生成
        content = self._generate_template(project_info)

        # 概要セクションをLLMで改善
        try:
            # 既存の概要を取得（テンプレート生成されたもの）
            existing_overview = self._get_project_overview_section(content)

            # RAGコンテキスト（改善されたクエリを使用）
            rag_context = ""
            if self.config.get("rag", {}).get("enabled", False):
                query = f"project overview for {self.project_root.name}"
                project_info_dict = {
                    "description": project_info.description,  # descriptionを追加
                    "key_features": project_info.key_features,
                    "dependencies": project_info.dependencies,
                }
                rag_context = self.rag_service.get_context(
                    query,
                    use_enhanced_query=True,
                    project_name=self.project_root.name,
                    languages=self.languages,
                    project_info=project_info_dict,
                )

            # プロンプト作成
            prompt = self._create_overview_prompt(project_info, existing_overview, rag_context)

            # 生成
            self.logger.info("LLMを使用して概要セクションを改善中...")
            new_overview = self.llm_service.generate(prompt)

            # クリーニング
            new_overview = self.formatting_service.clean_llm_output(new_overview)

            # 置換
            if new_overview:
                content = self._replace_overview_section(content, new_overview)

        except (LLMError, GenerationError) as e:
            self.logger.warning(f"ハイブリッド生成（概要改善）中にエラーが発生しました: {e}")
            # エラーが発生してもテンプレート生成されたコンテンツを返す
        except Exception as e:
            self.logger.warning(f"ハイブリッド生成中に予期しないエラーが発生しました: {e}", exc_info=True)
            # エラーが発生してもテンプレート生成されたコンテンツを返す

        return content
