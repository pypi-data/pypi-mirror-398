from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:
    try:
        import tomli as _tomli
        tomllib = _tomli  # type: ignore[assignment]
    except ImportError:
        tomllib = None  # type: ignore[assignment]

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


@dataclass
class TaskConfig:
    """タスク設定"""

    name: str
    enabled: bool = True
    continue_on_error: bool = False
    timeout: int | None = None
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class HookConfig:
    """フック設定"""

    name: str
    tasks: list[TaskConfig]
    enabled: bool = True


class ConfigLoader:
    """フック設定ローダー"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.hooks_config_path = self.project_root / "docgen" / "hooks.toml"
        self.hooks_yaml_path = self.project_root / "docgen" / "hooks.yaml"

    def load_config(self) -> dict[str, HookConfig]:
        """設定を読み込む"""
        config_data = self._read_config()
        hooks = {}

        hooks_data = config_data.get("hooks", {})
        for hook_name, hook_data in hooks_data.items():
            if not isinstance(hook_data, dict):
                continue

            tasks = []
            for task_data in hook_data.get("tasks", []):
                tasks.append(
                    TaskConfig(
                        name=task_data.get("name"),
                        enabled=task_data.get("enabled", True),
                        continue_on_error=task_data.get("continue_on_error", False),
                        timeout=task_data.get("timeout"),
                        params=task_data.get("params", {}),
                    )
                )

            hooks[hook_name] = HookConfig(
                name=hook_name, enabled=hook_data.get("enabled", True), tasks=tasks
            )

        return hooks

    def _read_config(self) -> dict[str, Any]:
        """TOMLまたはYAML設定ファイルを読み込む"""
        # TOML ファイルを優先
        if self.hooks_config_path.exists():
            return self._read_toml()

        # フォールバック: YAML ファイル
        if self.hooks_yaml_path.exists():
            print("Warning: hooks.yaml is deprecated. Please migrate to hooks.toml")
            return self._read_yaml()

        return {}

    def _read_toml(self) -> dict[str, Any]:
        """TOMLファイルを読み込む"""
        if tomllib is None:
            print("Warning: tomllib not available, falling back to YAML")
            return self._read_yaml()

        try:
            with open(self.hooks_config_path, "rb") as f:
                return tomllib.load(f) or {}
        except Exception as e:
            print(f"Warning: Failed to load hooks config (TOML): {e}")
            return {}

    def _read_yaml(self) -> dict[str, Any]:
        """YAMLファイルを読み込む（後方互換性用）"""
        if not self.hooks_yaml_path.exists():
            return {}

        if yaml is None:
            print("Warning: yaml library not available")
            return {}

        try:
            with open(self.hooks_yaml_path) as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Failed to load hooks config (YAML): {e}")
            return {}
