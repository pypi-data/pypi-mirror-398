"""
LanguageInfoCollectorのテスト
"""

from pathlib import Path

from docgen.collectors.language_info_collector import LanguageInfoCollector


class TestLanguageInfoCollector:
    """LanguageInfoCollectorクラスのテスト"""

    def test_collect_project_description_from_readme(self, temp_project):
        """READMEからのプロジェクト説明収集テスト"""
        readme = temp_project / "README.md"
        readme.write_text("""# My Awesome Project

This is a description of my awesome project. It does amazing things and solves real problems.

## Features

- Feature 1
- Feature 2
""")

        collector = LanguageInfoCollector(temp_project)
        description = collector.collect_project_description()

        assert description is not None
        assert "amazing things" in description

    def test_collect_project_description_from_setup_py(self, temp_project):
        """setup.pyからのプロジェクト説明収集テスト"""
        setup_py = temp_project / "setup.py"
        setup_py.write_text("""
from setuptools import setup

setup(
    name="my-project",
    description="A short description",
    long_description="A much longer description of the project that explains what it does and why it's useful.",
    author="Test Author"
)
""")

        collector = LanguageInfoCollector(temp_project)
        description = collector.collect_project_description()

        assert description is not None
        assert "A short description" in description

    def test_collect_project_description_from_package_json(self, temp_project):
        """package.jsonからのプロジェクト説明収集テスト"""
        package_json = temp_project / "package.json"
        package_json.write_text("""
{
  "name": "my-package",
  "description": "A JavaScript package description",
  "version": "1.0.0"
}
""")

        collector = LanguageInfoCollector(temp_project)
        description = collector.collect_project_description()

        assert description is not None and "JavaScript package description" in description
