"""
Detector Configuration Loader
"""

from pathlib import Path
from typing import Any

from .utils.logger import get_logger

logger = get_logger("config_manager")


class DetectorConfigLoader:
    """Loader for detector configurations"""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def load_defaults(self) -> dict[str, Any]:
        """
        Load default detector configurations

        Returns:
            Dictionary of language configurations
        """
        from .detectors.detector_patterns import DetectorPatterns
        from .models.detector import LanguageConfig, PackageManagerRule

        configs = {}
        for lang, extensions in DetectorPatterns.SOURCE_EXTENSIONS.items():
            pm_rules = []
            # Generate rules from patterns
            if lang in DetectorPatterns.PACKAGE_MANAGER_PATTERNS:
                patterns_list = DetectorPatterns.PACKAGE_MANAGER_PATTERNS[lang]
                if isinstance(patterns_list, list):
                    for patterns, manager in patterns_list:  # type: ignore[assignment]
                        files = patterns if isinstance(patterns, tuple) else (patterns,)
                        pm_rules.append(PackageManagerRule(files=files, manager=manager))

            configs[lang] = LanguageConfig(
                name=lang,
                extensions=tuple(extensions),
                package_files=tuple(DetectorPatterns.get_package_files(lang)),
                package_manager_rules=tuple(pm_rules),
            )
        return configs

    def load_user_overrides(self) -> dict[str, Any]:
        """
        Load detector configuration from config.toml

        Returns:
            Detector configuration dictionary
        """
        config_path = self.project_root / "config.toml"
        if not config_path.exists():
            return {}

        try:
            import importlib.util

            if importlib.util.find_spec("tomllib") is not None:
                import tomllib

                with open(config_path, "rb") as f:
                    config = tomllib.load(f)
            else:
                import tomli

                with open(config_path, "rb") as f:
                    config = tomli.load(f)
            return config.get("detectors", {})
        except Exception:
            return {}

    def merge_configs(self, defaults: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
        """
        Merge default and user configurations

        Args:
            defaults: Default configurations
            overrides: User configurations

        Returns:
            Merged configurations
        """
        merged = dict(defaults)

        for lang_name, override_config in overrides.items():
            if lang_name in merged:
                # Merge existing language config
                default_config = merged[lang_name]
                merged[lang_name] = self._merge_language_config(default_config, override_config)
            else:
                # Add new language config
                merged[lang_name] = override_config
                logger.info(f"Added new language config: {lang_name}")

        return merged

    def _merge_language_config(self, default: Any, override: Any) -> Any:
        """Merge two language configurations"""
        from .models.detector import LanguageConfig

        # Merge extensions and package files
        merged_extensions = tuple(set(default.extensions + override.extensions))
        merged_package_files = tuple(set(default.package_files + override.package_files))

        # Merge package manager rules (priority order)
        merged_rules = tuple(default.package_manager_rules + override.package_manager_rules)

        return LanguageConfig(
            name=default.name,
            extensions=merged_extensions,
            package_files=merged_package_files,
            package_manager_rules=merged_rules,
            custom_detector=override.custom_detector or default.custom_detector,
            custom_package_manager_detector=override.custom_package_manager_detector
            or default.custom_package_manager_detector,
        )
