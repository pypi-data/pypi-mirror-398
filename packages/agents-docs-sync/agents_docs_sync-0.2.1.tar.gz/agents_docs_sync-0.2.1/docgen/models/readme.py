"""README related Pydantic models."""

from pydantic import Field

from .base import DocgenBaseModel


class Dependencies(DocgenBaseModel):
    """Dependencies model."""

    python: list[str] | None = None
    nodejs: list[str] | None = None
    other: list[str] | None = None


class ReadmeSetupInstructions(DocgenBaseModel):
    """Setup instructions for README."""

    prerequisites: list[str] | None = None
    installation_steps: list[str] | None = None


class ReadmeConfig(DocgenBaseModel):
    """Configuration model for README documentation."""

    title: str = Field(description="プロジェクトタイトル")
    description: str = Field(description="プロジェクトの説明")
    technologies: list[str] = Field(description="使用技術のリスト")
    dependencies: Dependencies | None = Field(description="言語ごとの依存関係")
    setup_instructions: ReadmeSetupInstructions | None = None
    project_structure: list[str] | None = Field(default=None, description="プロジェクト構造の説明")
    key_features: list[str] | None = Field(default=None, description="主要機能")
    architecture: str | None = Field(default=None, description="アーキテクチャ")
    troubleshooting: str | None = Field(default=None, description="トラブルシューティング")
    build_commands: list[str] | None = Field(default=None, description="ビルドコマンド")
    test_commands: list[str] | None = Field(default=None, description="テストコマンド")
    manual_sections: dict[str, str] | None = Field(
        default=None, description="手動で記述されたセクション"
    )


class ReadmeDocument(DocgenBaseModel):
    """READMEドキュメントの構造化データモデル"""

    title: str = Field(description="プロジェクトタイトル")
    description: str = Field(description="プロジェクトの説明")
    technologies: list[str] = Field(description="使用技術のリスト")
    dependencies: Dependencies | None = Field(description="言語ごとの依存関係")
    setup_instructions: ReadmeSetupInstructions | None = None
    project_structure: list[str] | None = Field(default=None, description="プロジェクト構造の説明")
    key_features: list[str] | None = Field(default=None, description="主要機能")
    architecture: str | None = Field(default=None, description="アーキテクチャ")
    troubleshooting: str | None = Field(default=None, description="トラブルシューティング")
    build_commands: list[str] | None = Field(default=None, description="ビルドコマンド")
    test_commands: list[str] | None = Field(default=None, description="テストコマンド")
    manual_sections: dict[str, str] | None = Field(
        default=None, description="手動で記述されたセクション"
    )
