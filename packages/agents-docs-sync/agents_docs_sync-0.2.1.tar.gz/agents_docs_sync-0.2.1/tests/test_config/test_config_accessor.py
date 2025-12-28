"""
ConfigAccessor Tests
"""

from pathlib import Path

from docgen.config.config_accessor import ConfigAccessor


class TestConfigAccessor:
    """ConfigAccessor tests"""

    def test_default_values(self):
        """Test default values when config is empty"""
        config = {}
        accessor = ConfigAccessor(config)

        assert accessor.generate_api_doc is True
        assert accessor.update_readme is True
        assert accessor.generate_agents_doc is True
        assert accessor.llm_provider == "openai"
        assert accessor.llm_model == "gpt-4"
        assert accessor.output_dir == "docs"
        assert accessor.rag_enabled is False

    def test_custom_values(self):
        """Test custom values"""
        config = {
            "generation": {
                "generate_api_doc": False,
                "update_readme": False,
                "generate_agents_doc": False,
            },
            "llm": {
                "provider": "anthropic",
                "model": "claude-3-opus",
                "temperature": 0.7,
            },
            "output": {
                "dir": "documentation",
                "api_doc_dir": "reference",
            },
            "rag": {
                "enabled": True,
            },
        }
        accessor = ConfigAccessor(config)

        assert accessor.generate_api_doc is False
        assert accessor.update_readme is False
        assert accessor.generate_agents_doc is False
        assert accessor.llm_provider == "anthropic"
        assert accessor.llm_model == "claude-3-opus"
        assert accessor.llm_temperature == 0.7
        assert accessor.output_dir == "documentation"
        assert accessor.api_doc_dir == "reference"
        assert accessor.rag_enabled is True
