"""
Coding standards collector module
Collects coding standards from various configuration files.
"""

from pathlib import Path
from typing import Any

from ..utils.logger import get_logger


class CodingStandardsCollector:
    """Coding standards collector class"""

    PYPROJECT_TOML = "pyproject.toml"
    EDITORCONFIG = ".editorconfig"
    PRETTIER_FILES = [".prettierrc", "prettier.config.js", ".prettierrc.json"]

    def __init__(self, project_root: Path, logger: Any | None = None):
        """
        Initialize

        Args:
            project_root: Project root directory
            logger: Logger instance
        """
        self.project_root = project_root
        self.logger = logger or get_logger(__name__)

    def collect_coding_standards(self) -> dict[str, str | dict[str, Any] | bool]:
        """
        Collect coding standards

        Returns:
            Dictionary of coding standards
        """
        standards: dict[str, str | dict[str, Any] | bool] = {}

        # Collect from pyproject.toml
        pyproject = self.project_root / self.PYPROJECT_TOML
        if pyproject.exists():
            try:
                # Use standard library tomllib for Python 3.11+
                import sys

                if sys.version_info >= (3, 11):
                    import tomllib

                    with open(pyproject, "rb") as f:
                        data = tomllib.load(f)
                else:
                    # Use tomli for Python 3.10 and earlier (optional)
                    try:
                        import tomli

                        with open(pyproject, "rb") as f:
                            data = tomli.load(f)
                    except ImportError:
                        # Fallback if tomli is not installed
                        raise ImportError("tomli not available") from None

                if "tool" in data:
                    tools = data["tool"]
                    if "black" in tools:
                        standards["formatter"] = "black"
                        standards["black_config"] = tools["black"]
                    if "isort" in tools:
                        standards["import_sorter"] = "isort"
                        standards["isort_config"] = tools["isort"]
                    if "ruff" in tools:
                        standards["linter"] = "ruff"
                        standards["ruff_config"] = tools["ruff"]
            except ImportError as e:
                self.logger.warning(
                    f"TOML library not available: {e}. Falling back to simple parsing."
                )
                # Fallback to simple parsing if TOML parsing fails
                content = pyproject.read_text(encoding="utf-8")
                if "black" in content:
                    standards["formatter"] = "black"
                if "ruff" in content:
                    standards["linter"] = "ruff"
            except Exception as e:
                self.logger.warning(
                    f"Failed to parse pyproject.toml: {e}. Falling back to simple parsing."
                )
                # Fallback to simple parsing if TOML parsing fails
                content = pyproject.read_text(encoding="utf-8")
                if "black" in content:
                    standards["formatter"] = "black"
                if "ruff" in content:
                    standards["linter"] = "ruff"

        # Collect from .editorconfig
        editorconfig = self.project_root / self.EDITORCONFIG
        if editorconfig.exists():
            standards["editorconfig"] = True

        # Collect from prettier.config.js or .prettierrc
        for prettier_file in self.PRETTIER_FILES:
            prettier_path = self.project_root / prettier_file
            if prettier_path.exists():
                standards["formatter"] = "prettier"
                break

        return standards
