"""Detector configuration models."""

from collections.abc import Callable
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class PackageManagerRule(BaseModel):
    """Package manager detection rule."""

    files: tuple[str, ...] = Field(description="Files required for detection (all must exist)")
    manager: str = Field(description="Package manager name")
    priority: int = Field(default=5, ge=0, description="Priority (higher is better)")
    needs_content_check: bool = Field(
        default=False, description="Whether file content check is needed"
    )

    @field_validator("files")
    @classmethod
    def validate_files(cls, v: tuple[str, ...]) -> tuple[str, ...]:
        if not v:
            raise ValueError("files must not be empty")
        return v

    @field_validator("manager")
    @classmethod
    def validate_manager(cls, v: str) -> str:
        if not v:
            raise ValueError("manager must not be empty")
        return v


class LanguageConfig(BaseModel):
    """Language detection configuration."""

    name: str = Field(description="Language name")
    extensions: tuple[str, ...] = Field(default_factory=tuple, description="Source file extensions")
    package_files: tuple[str, ...] = Field(
        default_factory=tuple, description="Package management files"
    )
    package_manager_rules: tuple[PackageManagerRule, ...] = Field(
        default_factory=tuple, description="Package manager detection rules"
    )

    # Special detection logic (optional) - excluded from serialization
    custom_detector: Callable[[Path], bool] | None = Field(default=None, exclude=True)
    custom_package_manager_detector: Callable[[Path], str | None] | None = Field(
        default=None, exclude=True
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v:
            raise ValueError("name must not be empty")
        return v

    def get_sorted_package_manager_rules(self) -> list[PackageManagerRule]:
        """Return package manager rules sorted by priority."""
        return sorted(self.package_manager_rules, key=lambda r: r.priority, reverse=True)
