"""Common utilities for collecting project information."""

import json
from pathlib import Path
from typing import Any

from ..utils.file_utils import safe_read_file


class ConfigReader:
    """Common utilities for reading various configuration files."""

    @staticmethod
    def read_json_file(file_path: Path) -> dict[str, Any] | None:
        """Read and parse JSON file."""
        content = safe_read_file(file_path)
        if content:
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return None
        return None

    @staticmethod
    def read_makefile(project_root: Path) -> str | None:
        """Read Makefile content."""
        makefile_paths = ["Makefile", "makefile"]
        for makefile in makefile_paths:
            content = safe_read_file(project_root / makefile)
            if content:
                return content
        return None

    @staticmethod
    def read_package_json(project_root: Path) -> dict[str, Any] | None:
        """Read package.json file."""
        return ConfigReader.read_json_file(project_root / "package.json")


class BuildCommandCollector:
    """ビルドコマンド収集クラス"""

    def __init__(self, project_root: Path, package_managers: dict[str, str] | None = None):
        self.project_root = project_root
        self.package_managers = package_managers or {}

    def _add_uv_run_if_needed(self, command: str) -> str:
        """uvパッケージマネージャを使用している場合、python/pytestコマンドにuv runを追加"""
        if "python" in self.package_managers and self.package_managers["python"] == "uv":
            if command.startswith("python") or command.startswith("pytest"):
                return f"uv run {command}"
        return command

    def collect_build_commands(self) -> list[str]:
        """ビルドコマンドを収集"""
        commands = []

        # Pythonプロジェクトの場合
        if "python" in self.package_managers:
            pm = self.package_managers["python"]
            if pm == "uv":
                commands.append("uv sync")
                commands.append("uv build")
            elif pm == "poetry":
                commands.append("poetry install")
                commands.append("poetry build")
            elif pm == "conda":
                commands.append("conda env create -f environment.yml")
            else:  # pip
                commands.append("pip install -e .")
                commands.append("python setup.py build")

        # scripts/run_pipeline.sh から収集
        pipeline_script = self.project_root / "scripts" / "run_pipeline.sh"
        if pipeline_script.exists():
            content = safe_read_file(pipeline_script)
            if content:
                for line in content.split("\n"):
                    if (
                        line.strip().startswith("python")
                        or line.strip().startswith("npm")
                        or line.strip().startswith("make")
                        or line.strip().startswith("go")
                    ):
                        command = line.strip()
                        command = self._add_uv_run_if_needed(command)
                        commands.append(command)

        # Makefile から収集
        content = ConfigReader.read_makefile(self.project_root)
        if content:
            for line in content.split("\n"):
                if line.startswith("\t") and line.strip():
                    command = line.lstrip("\t")
                    if command and not command.startswith("@"):
                        command = self._add_uv_run_if_needed(command)
                        commands.append(command)

        # package.json から収集
        package_data = ConfigReader.read_package_json(self.project_root)
        if package_data and "scripts" in package_data:
            pm = self.package_managers.get("javascript", "npm")
            for script_name, script_cmd in package_data["scripts"].items():
                if pm == "pnpm":
                    commands.append(f"pnpm run {script_name}")
                elif pm == "yarn":
                    commands.append(f"yarn run {script_name}")
                else:  # npm
                    commands.append(f"npm run {script_name}")

        # Goプロジェクトの場合
        if "go" in self.package_managers:
            pm = self.package_managers["go"]
            if pm == "go":
                commands.append("go build")
            elif pm == "dep":
                commands.append("dep ensure")
            elif pm == "glide":
                commands.append("glide install")

        # 重複を順序を保って排除
        seen = set()
        unique_commands = []
        for c in commands:
            if c not in seen:
                unique_commands.append(c)
                seen.add(c)
        return unique_commands

    @staticmethod
    def read_pyproject_toml(project_root: Path) -> dict[str, Any] | None:
        """Read pyproject.toml file."""
        try:
            import tomllib
        except ImportError:
            return None

        file_path = project_root / "pyproject.toml"
        try:
            with open(file_path, "rb") as f:
                return tomllib.load(f)
        except (OSError, ValueError):
            return None

    @staticmethod
    def extract_scripts_from_package_json(package_data: dict[str, Any]) -> list[str]:
        """Extract scripts from package.json."""
        scripts = package_data.get("scripts", {})
        return list(scripts.keys())

    @staticmethod
    def extract_dependencies_from_package_json(
        package_data: dict[str, Any],
    ) -> dict[str, list[str]]:
        """Extract dependencies from package.json."""
        deps = {}

        # Regular dependencies
        if "dependencies" in package_data:
            deps["npm"] = list(package_data["dependencies"].keys())

        # Dev dependencies
        if "devDependencies" in package_data:
            deps.setdefault("npm-dev", []).extend(package_data["devDependencies"].keys())

        return deps

    @staticmethod
    def parse_makefile_targets(content: str) -> list[str]:
        """Parse Makefile targets."""
        targets = []
        for line in content.split("\n"):
            line = line.strip()
            if line and not line.startswith("\t") and not line.startswith("#") and ":" in line:
                target = line.split(":")[0].strip()
                if target and not target.startswith("."):
                    targets.append(target)
        return targets

    @staticmethod
    def detect_language_from_config(project_root: Path) -> str | None:
        """Detect programming language from configuration files."""
        # Python
        if (project_root / "pyproject.toml").exists() or (project_root / "setup.py").exists():
            return "python"

        # JavaScript/TypeScript
        package_json = ConfigReader.read_package_json(project_root)
        if package_json:
            return "javascript"  # Could be refined to detect TypeScript

        # Go
        if (project_root / "go.mod").exists():
            return "go"

        # Rust
        if (project_root / "Cargo.toml").exists():
            return "rust"

        return None


class TestingCommandScanner:
    """Test command scanner class"""

    SCRIPTS_DIR = "scripts"
    RUN_TESTS_SCRIPT = "run_tests.sh"
    MAKEFILE_NAMES = ["Makefile", "makefile"]
    PYTEST_INI = "pytest.ini"
    PACKAGE_JSON = "package.json"

    def __init__(
        self,
        project_root: Path,
        package_managers: dict[str, str] | None = None,
        logger: Any | None = None,
    ):
        """
        Initialize

        Args:
            project_root: Project root directory
            package_managers: Dictionary of detected package managers
            logger: Logger instance
        """
        self.project_root = project_root
        self.package_managers = package_managers or {}
        self.logger = logger
        self.build_collector = BuildCommandCollector(project_root, package_managers)

    def collect_test_commands(self) -> list[str]:
        """
        Collect test commands

        Returns:
            List of test commands
        """
        commands = []

        # Collect from scripts/run_tests.sh
        run_tests_script = self.project_root / self.SCRIPTS_DIR / self.RUN_TESTS_SCRIPT
        if run_tests_script.exists():
            # If the script exists, it's the primary test command
            # We can read it to see what it does, or just return the script execution
            # For now, let's return the content if it's a single line command, or the script itself
            try:
                content = run_tests_script.read_text(encoding="utf-8").strip()
                lines = [
                    line
                    for line in content.splitlines()
                    if line.strip() and not line.startswith("#")
                ]
                if len(lines) == 1:
                    command = lines[0]
                    command = self.build_collector._add_uv_run_if_needed(command)
                    commands.append(command)
                else:
                    # If it's a complex script, return the script execution command
                    commands.append(f"bash {self.SCRIPTS_DIR}/{self.RUN_TESTS_SCRIPT}")
            except Exception:
                pass

        # Collect from Makefile
        makefile = self.project_root / self.MAKEFILE_NAMES[0]
        if makefile.exists():
            content = makefile.read_text(encoding="utf-8")
            # Extract command line for test target
            in_test_target = False
            for line in content.split("\n"):
                if line.strip() == "test:":
                    in_test_target = True
                elif line.strip().endswith(":") and in_test_target:
                    break  # Next target
                elif in_test_target and line.startswith("\t") and line.strip():
                    command = line.lstrip("\t")
                    if command and not command.startswith("@"):
                        command = self.build_collector._add_uv_run_if_needed(command)
                        commands.append(command)

        # For Python projects
        if "python" in self.package_managers:
            pm = self.package_managers["python"]
            if pm == "uv":
                commands.append("uv run pytest tests/ -v --tb=short")
            elif pm == "poetry":
                commands.append("poetry run pytest tests/ -v --tb=short")
            else:  # pip
                commands.append("pytest tests/ -v --tb=short")
        # Collect from pytest.ini (if package manager is not specified)
        elif (self.project_root / self.PYTEST_INI).exists():
            command = "pytest tests/ -v --tb=short"
            command = self.build_collector._add_uv_run_if_needed(command)
            commands.append(command)

        # Collect from package.json
        if (self.project_root / self.PACKAGE_JSON).exists():
            package_data = ConfigReader.read_package_json(self.project_root)
            if package_data and "scripts" in package_data and "test" in package_data["scripts"]:
                pm = self.package_managers.get("javascript", "npm")
                if pm == "pnpm":
                    commands.append("pnpm test")
                elif pm == "yarn":
                    commands.append("yarn test")
                else:  # npm
                    commands.append("npm test")

        # For Go projects
        if "go" in self.package_managers and (self.project_root / "go.mod").exists():
            pm = self.package_managers["go"]
            if pm == "go":
                commands.append("go test ./...")

        # Deduplicate preserving order
        seen = set()
        unique_commands = []
        for c in commands:
            if c not in seen:
                unique_commands.append(c)
                seen.add(c)
        return unique_commands
