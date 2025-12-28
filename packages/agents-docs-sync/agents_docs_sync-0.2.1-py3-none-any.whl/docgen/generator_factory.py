"""ジェネレーターファクトリーモジュール"""

from pathlib import Path
from typing import Any

from .generators.base_generator import BaseGenerator
from .utils.logger import get_logger

logger = get_logger("generator_factory")


class GeneratorFactory:
    """ジェネレーターのファクトリークラス"""

    # Keep names to allow patching of symbols like APIGenerator, ReadmeGenerator, AgentsGenerator
    _generators = {
        "api": "APIGenerator",
        "readme": "ReadmeGenerator",
        "agents": "AgentsGenerator",
        "contributing": "ContributingGenerator",
    }

    @classmethod
    def create_generator(
        cls,
        generator_type: str,
        project_root: Path,
        detected_languages: list[str],
        config: dict[str, Any],
        detected_package_managers: dict[str, str] | None = None,
    ) -> BaseGenerator:
        """指定されたタイプのジェネレーターを作成"""
        class_name = cls._generators.get(generator_type)
        if class_name is None:
            raise ValueError(f"Unknown generator type: {generator_type}")

        # Import the generator class dynamically
        GeneratorClass: type[BaseGenerator]
        if generator_type == "api":
            from .generators.api_generator import APIGenerator as GeneratorClass
        elif generator_type == "readme":
            from .generators.readme_generator import ReadmeGenerator as GeneratorClass
        elif generator_type == "agents":
            from .generators.agents_generator import AgentsGenerator as GeneratorClass
        elif generator_type == "contributing":
            from .generators.contributing_generator import ContributingGenerator as GeneratorClass
        else:
            raise ValueError(f"Unknown generator type: {generator_type}")

        return GeneratorClass(project_root, detected_languages, config, detected_package_managers)

    @classmethod
    def get_available_generators(cls) -> list[str]:
        """利用可能なジェネレーターのリストを取得"""
        return list(cls._generators.keys())
