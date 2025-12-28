"""
GeneratorFactoryのテスト
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from docgen.generator_factory import GeneratorFactory


class TestGeneratorFactory:
    """GeneratorFactoryクラスのテスト"""

    def test_create_generator_api(self, temp_project):
        config = {"output": {"api_doc": "docs/api.md"}}

        with patch("docgen.generators.api_generator.APIGenerator") as mock_api:
            mock_instance = MagicMock()
            mock_api.return_value = mock_instance

            generator = GeneratorFactory.create_generator("api", temp_project, ["python"], config)

            assert generator == mock_instance
            mock_api.assert_called_once_with(temp_project, ["python"], config, None)

    def test_create_generator_readme(self, temp_project):
        config = {"output": {"readme": "README.md"}}

        with patch("docgen.generators.readme_generator.ReadmeGenerator") as mock_readme:
            mock_instance = MagicMock()
            mock_readme.return_value = mock_instance

            generator = GeneratorFactory.create_generator(
                "readme", temp_project, ["python"], config
            )

            assert generator == mock_instance
            mock_readme.assert_called_once_with(temp_project, ["python"], config, None)

    def test_create_generator_agents(self, temp_project):
        config = {"output": {"agents_doc": "AGENTS.md"}}

        with patch("docgen.generators.agents_generator.AgentsGenerator") as mock_agents:
            mock_instance = MagicMock()
            mock_agents.return_value = mock_instance

            generator = GeneratorFactory.create_generator(
                "agents", temp_project, ["python"], config
            )

            assert generator == mock_instance
            mock_agents.assert_called_once_with(temp_project, ["python"], config, None)


def test_create_generator_commit_message(temp_project):
    """Unknown generator type for commit_message"""
    config = {"agents": {"llm_mode": "api"}}
    with pytest.raises(ValueError) as exc:
        GeneratorFactory.create_generator("commit_message", temp_project, ["python"], config)
    assert "Unknown generator type: commit_message" in str(exc.value)


def test_create_generator_unknown_type(temp_project):
    """Unknown generator type test"""
    config = {}
    with pytest.raises(ValueError) as exc:
        GeneratorFactory.create_generator("unknown", temp_project, ["python"], config)
    assert "Unknown generator type: unknown" in str(exc.value)
