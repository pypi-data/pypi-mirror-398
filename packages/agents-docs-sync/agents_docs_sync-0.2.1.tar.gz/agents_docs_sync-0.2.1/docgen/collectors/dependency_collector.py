"""
Dependency collector module
Collects project dependencies from various configuration files.
"""

from pathlib import Path
from typing import Any

from ..utils.file_utils import safe_read_json
from ..utils.logger import get_logger


class DependencyCollector:
    """Dependency collector class"""

    REQUIREMENTS_FILES = ["requirements.txt", "requirements-docgen.txt", "requirements-test.txt"]
    PACKAGE_JSON = "package.json"
    GO_MOD = "go.mod"

    def __init__(self, project_root: Path, logger: Any | None = None):
        """
        Initialize

        Args:
            project_root: Project root directory
            logger: Logger instance
        """
        self.project_root = project_root
        self.logger = logger or get_logger(__name__)

    def collect_dependencies(self) -> dict[str, list[str]]:
        """
        Collect dependencies

        Returns:
            Dictionary of dependencies per language
        """
        dependencies = {}

        # Python dependencies
        python_deps = []
        for req_file in self.REQUIREMENTS_FILES:
            req_path = self.project_root / req_file
            if req_path.exists():
                with open(req_path, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            python_deps.append(line)
        if python_deps:
            dependencies["python"] = python_deps

        # Node.js dependencies
        package_data = safe_read_json(self.project_root / self.PACKAGE_JSON)
        if package_data and "dependencies" in package_data:
            node_deps = [
                f"{name}@{version}" for name, version in package_data["dependencies"].items()
            ]
            dependencies["nodejs"] = node_deps

        # Go dependencies
        go_mod = self.project_root / self.GO_MOD
        if go_mod.exists():
            go_deps = []
            try:
                content = go_mod.read_text(encoding="utf-8")
                lines = content.split("\n")
                in_require = False
                for line in lines:
                    line = line.strip()
                    if line.startswith("require ("):
                        in_require = True
                        continue
                    if in_require and line == ")":
                        in_require = False
                        continue
                    if in_require or line.startswith("require "):
                        if in_require:
                            parts = line.split()
                            if parts:
                                go_deps.append(parts[0])
                        else:
                            parts = line.split()
                            if len(parts) >= 2:
                                go_deps.append(parts[1])
                if go_deps:
                    dependencies["go"] = go_deps
            except Exception as e:
                self.logger.warning(f"Failed to parse go.mod: {e}")

        # Deduplicate preserving order
        if "python" in dependencies:
            dependencies["python"] = self._dedup_preserve_order(dependencies["python"])
        if "nodejs" in dependencies:
            dependencies["nodejs"] = self._dedup_preserve_order(dependencies["nodejs"])
        if "go" in dependencies:
            dependencies["go"] = self._dedup_preserve_order(dependencies["go"])

        return dependencies

    def _dedup_preserve_order(self, items: list[str]) -> list[str]:
        """Deduplicate list preserving order"""
        seen_local = set()
        out = []
        for it in items:
            if it not in seen_local:
                out.append(it)
                seen_local.add(it)
        return out
