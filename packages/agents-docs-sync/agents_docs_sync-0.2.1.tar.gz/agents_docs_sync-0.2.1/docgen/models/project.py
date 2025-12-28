"""Project related Pydantic models."""

from typing import Any

from pydantic import Field

from .base import DocgenBaseModel


class ProjectInfo(DocgenBaseModel):
    """Project information model."""

    description: str | None = None
    build_commands: list[str] = Field(default_factory=list)
    test_commands: list[str] = Field(default_factory=list)
    dependencies: dict[str, list[str]] = Field(default_factory=dict)
    coding_standards: dict[str, Any] | None = None
    ci_cd_info: dict[str, Any] | None = None
    project_structure: dict[str, Any] | None = None
    key_features: list[str] | None = Field(default=None, description="主要機能")
    scripts: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="実行可能なスクリプト (name -> {command, description, options})",
    )
