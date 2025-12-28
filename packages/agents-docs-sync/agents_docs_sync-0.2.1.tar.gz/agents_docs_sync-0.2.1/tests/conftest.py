import os
from pathlib import Path
import shutil
import tempfile

import pytest

# Set environment variable for testing at module level to ensure it's set before logger initialization
os.environ["DOCGEN_TESTING"] = "1"

# Project root is now handled by pytest.ini/pythonpath configuration
PROJECT_ROOT = Path(__file__).parent.parent.resolve()


@pytest.fixture(autouse=True)
def set_test_env():
    """Ensure environment variable is set (redundant but safe)."""
    os.environ["DOCGEN_TESTING"] = "1"
    yield
    # Do not remove it as other tests might need it if run in same process
    # But for safety we can keep it. Or we can just rely on module level.
    # Let's keep the fixture to be explicit about scope if needed, but module level is key.


@pytest.fixture(scope="function")
def temp_project():
    """Create a temporary project directory with basic structure."""
    temp_dir = Path(tempfile.mkdtemp())

    (temp_dir / "docgen").mkdir()
    (temp_dir / "docgen" / "config.toml").write_text("""
[output]
agents_doc = "AGENTS.md"
api_doc = "api.md"
readme = "README.md"

[agents]
llm_mode = "both"

[agents.api]
provider = "openai"
api_key_env = "OPENAI_API_KEY"

[agents.local]
provider = "ollama"
model = "llama3"
base_url = "http://localhost:11434"

[project]
name = "test-project"
description = "Test project for agents-docs-sync"
languages = ["python"]
""")
    yield temp_dir

    # Clean up
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="function")
def sample_config():
    """Return a sample configuration dictionary."""
    return {
        "output": {"agents_doc": "AGENTS.md", "api_doc": "api.md", "readme": "README.md"},
        "agents": {
            " llm_mode": "both",
            "api": {"provider": "openai", "api_key_env": "OPENAI_API_KEY"},
            "local": {
                "provider": "ollama",
                "model": "llama3",
                "base_url": "http://localhost:11434",
            },
        },
        "project": {
            "name": "test-project",
            "description": "Test project for agents-docs-sync",
            "languages": ["python"],
        },
    }


@pytest.fixture(scope="function")
def mock_llm_client(mocker):
    """Mock LLMクライアント"""
    mock_client = mocker.Mock()
    mock_client.generate.return_value = "Mocked LLM response"
    return mock_client


@pytest.fixture(scope="function")
def sample_project_root(tmp_path):
    """
    Create a complete sample project structure for testing

    Returns:
        Path: Root directory of the sample project
    """
    project_root = tmp_path / "sample_project"
    project_root.mkdir()

    # Basic Python project structure
    (project_root / "src").mkdir()
    (project_root / "src" / "__init__.py").touch()
    (project_root / "src" / "main.py").write_text('def main():\n    print("Hello, World!")\n')

    # pyproject.toml
    (project_root / "pyproject.toml").write_text(
        '[project]\nname = "sample-project"\nversion = "0.1.0"\n'
    )

    # docgen configuration
    (project_root / "docgen").mkdir()
    (project_root / "docgen" / "config.toml").write_text('[output]\nagents_doc = "AGENTS.md"\n')

    return project_root


@pytest.fixture(scope="function")
def mock_config():
    """
    Mock configuration object for testing

    Returns:
        dict: Configuration dictionary
    """
    return {
        "output": {
            "agents_doc": "AGENTS.md",
            "api_doc": "API.md",
            "readme": "README.md",
        },
        "generation": {
            "generate_api_doc": True,
            "update_readme": True,
        },
        "llm": {
            "provider": "openai",
            "model": "gpt-4",
        },
    }


@pytest.fixture(scope="function")
def mock_services(mocker, mock_config):
    """
    Create mock service container with all services

    Returns:
        dict: Dictionary of mocked services
    """
    from docgen.generators.services import (
        FormattingService,
        LLMService,
        ManualSectionService,
        TemplateService,
    )

    mock_llm = mocker.Mock(spec=LLMService)
    mock_template = mocker.Mock(spec=TemplateService)
    mock_formatting = mocker.Mock(spec=FormattingService)
    mock_manual = mocker.Mock(spec=ManualSectionService)

    # Set default return values
    mock_llm.generate.return_value = "Generated content"
    mock_template.render.return_value = "Rendered content"
    mock_formatting.format_markdown.return_value = "Formatted content"

    return {
        "llm": mock_llm,
        "template": mock_template,
        "formatting": mock_formatting,
        "manual": mock_manual,
    }


@pytest.fixture(scope="function")
def mock_project_info():
    """
    Create mock ProjectInfo data for testing

    Returns:
        ProjectInfo: Mock project information
    """
    from docgen.models.project import ProjectInfo

    return ProjectInfo(
        name="test-project",
        description="A test project",
        version="1.0.0",
        languages=["python"],
        frameworks=[],
        package_managers={},
        dependencies=[],
        dev_dependencies=[],
    )
