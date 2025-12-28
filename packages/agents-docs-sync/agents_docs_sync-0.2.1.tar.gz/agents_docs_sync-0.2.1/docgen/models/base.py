"""Base model for all docgen Pydantic models."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class DocgenBaseModel(BaseModel):
    """Base model for all docgen models.

    Provides common configuration and methods for all Pydantic models
    used throughout the docgen system.

    Features:
    - Extra fields forbidden to catch typos
    - Assignment validation enabled
    - Enum values automatically used
    - Template context conversion method
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        use_enum_values=True,
    )

    def to_template_context(self) -> dict[str, Any]:
        """Convert model to template rendering context.

        Returns:
            Dictionary suitable for Jinja2 template rendering.
        """
        return self.model_dump()
