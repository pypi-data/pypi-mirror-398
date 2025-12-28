"""Agents related Pydantic models."""

from typing import Any, Union

from pydantic import Field

from .base import DocgenBaseModel


class LLMConfig(DocgenBaseModel):
    """LLM設定モデル"""

    provider: str | None = Field(
        default=None, description="LLMプロバイダー (openai, anthropic, ollama, local)"
    )
    model: str | None = Field(default=None, description="モデル名")
    api_key: str | None = Field(default=None, description="APIキー")
    api_key_env: str | None = Field(default=None, description="APIキー環境変数名")
    base_url: str | None = Field(default=None, description="ベースURL")
    endpoint: str | None = Field(default=None, description="エンドポイントURL")
    timeout: int = Field(default=30, description="タイムアウト秒数")
    max_retries: int = Field(default=3, description="最大リトライ回数")
    retry_delay: float = Field(default=1.0, description="リトライ遅延秒数")
    temperature: float | None = Field(default=None, description="温度パラメータ")
    max_tokens: int | None = Field(default=None, description="最大トークン数")


class ProjectOverview(DocgenBaseModel):
    """Project overview model."""

    name: str
    languages: list[str]
    dependencies: list[str] | None = None


class LLMSetup(DocgenBaseModel):
    """LLM setup model."""

    api_setup: str | None = None
    local_setup: str | None = None


class SetupInstructions(DocgenBaseModel):
    """Setup instructions model."""

    prerequisites: list[str] | None = None
    installation_commands: list[str] | None = None
    llm_setup: LLMSetup | None = None


class BuildTestInstructions(DocgenBaseModel):
    """Build and test instructions model."""

    build_commands: list[str] | None = None
    test_commands: list[str] | None = None
    test_execution_notes: str | None = None


class CodingStandards(DocgenBaseModel):
    """Coding standards model."""

    standards: list[str] | None = None
    notes: str | None = None


class PRGuidelines(DocgenBaseModel):
    """PR guidelines model."""

    branch_creation: str | None = None
    commit_guidelines: str | None = None
    pr_creation: str | None = None


class AgentsConfig(DocgenBaseModel):
    """Configuration model for agents documentation."""

    title: str = Field(description="ドキュメントのタイトル")
    description: str = Field(description="プロジェクトの説明")
    project_overview: ProjectOverview
    setup_instructions: SetupInstructions
    build_test_instructions: BuildTestInstructions
    coding_standards: CodingStandards | None = None
    pr_guidelines: PRGuidelines | None = None
    project_structure: str | None = Field(default=None, description="プロジェクト構造")
    key_features: list[str] | None = Field(default=None, description="主要機能")
    architecture: str | None = Field(default=None, description="アーキテクチャ")
    troubleshooting: str | None = Field(default=None, description="トラブルシューティング")
    auto_generated_note: str | None = Field(default=None, description="自動生成に関する注意書き")


class AgentsGenerationConfig(DocgenBaseModel):
    """Agents generation configuration model."""

    agents_mode: str = "template"
    readme_mode: str = "template"
    enable_commit_message: bool = True


class AgentsConfigSection(DocgenBaseModel):
    """Agents configuration section model."""

    llm_mode: str = "both"
    generation: AgentsGenerationConfig = Field(default_factory=AgentsGenerationConfig)
    api: Union["LLMConfig", None] = Field(default=None, description="API LLM設定")
    local: Union["LLMConfig", None] = Field(default=None, description="ローカルLLM設定")
    coding_standards: dict[str, Any] | None = Field(
        default=None, description="コーディング規約設定"
    )
    custom_instructions: str | None = Field(default=None, description="プロジェクト固有の指示")


class AgentsDocument(DocgenBaseModel):
    """AGENTS.mdドキュメントの構造化データモデル"""

    title: str = Field(description="ドキュメントのタイトル")
    description: str = Field(description="プロジェクトの説明")
    project_overview: ProjectOverview
    setup_instructions: SetupInstructions
    build_test_instructions: BuildTestInstructions
    coding_standards: CodingStandards | None = None
    pr_guidelines: PRGuidelines | None = None
    project_structure: str | None = Field(default=None, description="プロジェクト構造")
    key_features: list[str] | None = Field(default=None, description="主要機能")
    architecture: str | None = Field(default=None, description="アーキテクチャ")
    troubleshooting: str | None = Field(default=None, description="トラブルシューティング")
    auto_generated_note: str = Field(description="自動生成に関する注意書き")
