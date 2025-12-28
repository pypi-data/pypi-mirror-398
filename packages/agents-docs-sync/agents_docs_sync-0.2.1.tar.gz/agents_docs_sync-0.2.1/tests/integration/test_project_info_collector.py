"""
ProjectInfoCollectorのテスト
"""

from pathlib import Path
from unittest.mock import patch

from docgen.collectors.project_info_collector import ProjectInfoCollector


class TestProjectInfoCollector:
    """ProjectInfoCollectorクラスのテスト"""

    def test_project_info_collector_initialization(self, temp_project):
        """ProjectInfoCollectorの初期化テスト"""
        collector = ProjectInfoCollector(temp_project)

        assert collector.project_root == temp_project

    def test_project_info_collector_initialization_with_package_managers(self, temp_project):
        """パッケージマネージャ付き初期化テスト"""
        package_managers = {"python": "uv", "javascript": "npm"}
        collector = ProjectInfoCollector(temp_project, package_managers)

        assert collector.project_root == temp_project
        assert collector.package_managers == package_managers

    def test_collect_all(self, temp_project):
        """全情報収集テスト"""
        collector = ProjectInfoCollector(temp_project)

        # LanguageInfoCollectorのモック
        with patch.object(
            collector.language_info_collector,
            "collect",
            return_value={
                "description": "Test project",
                "scripts": {"test": {"command": "npm test", "description": "", "options": []}},
            },
        ):
            with patch.object(
                collector.build_collector, "collect_build_commands", return_value=["make build"]
            ):
                with patch.object(collector, "collect_test_commands", return_value=["make test"]):
                    with patch.object(
                        collector, "collect_dependencies", return_value={"python": ["pytest"]}
                    ):
                        with patch.object(
                            collector,
                            "collect_coding_standards",
                            return_value={"formatter": "black"},
                        ):
                            with patch.object(
                                collector,
                                "collect_ci_cd_info",
                                return_value={"github_actions": True},
                            ):
                                with patch.object(
                                    collector,
                                    "collect_project_structure",
                                    return_value={"directories": ["src"], "files": ["main.py"]},
                                ):
                                    result = collector.collect_all()

                                    from docgen.models import ProjectInfo

                                    expected = ProjectInfo(
                                        description="Test project",
                                        build_commands=["make build"],
                                        test_commands=["make test"],
                                        dependencies={"python": ["pytest"]},
                                        coding_standards={"formatter": "black"},
                                        ci_cd_info={"github_actions": True},
                                        project_structure={
                                            "directories": ["src"],
                                            "files": ["main.py"],
                                        },
                                        key_features=[],
                                        scripts={
                                            "test": {
                                                "command": "npm test",
                                                "description": "",
                                                "options": [],
                                            }
                                        },
                                    )

                                    assert result == expected

    # ... (other tests remain unchanged) ...

    def test_collect_test_commands_with_package_managers(self, temp_project):
        """パッケージマネージャ考慮のテストコマンド収集テスト"""
        # Pythonプロジェクト (uv)
        collector = ProjectInfoCollector(temp_project, {"python": "uv"})
        commands = collector.collect_test_commands()
        assert "uv run pytest tests/ -v --tb=short" in commands

        # Poetryプロジェクト
        collector = ProjectInfoCollector(temp_project, {"python": "poetry"})
        commands = collector.collect_test_commands()
        assert "poetry run pytest tests/ -v --tb=short" in commands

        # JavaScriptプロジェクト
        # 前のテストの影響を受けないようにクリーンアップが必要だが、
        # temp_projectはfunction scopeなので、このメソッド内での変更は持続する
        # ファイルを作成する前にクリーンアップするか、上書きする

        package_json = temp_project / "package.json"
        package_json.write_text('{"scripts": {"test": "jest"}}')

        collector = ProjectInfoCollector(temp_project, {"javascript": "yarn"})
        commands = collector.collect_test_commands()
        assert "yarn test" in commands

        # Goプロジェクト
        # package.jsonを削除してGoのテストに影響しないようにする
        if package_json.exists():
            package_json.unlink()
        # Goプロジェクト
        (temp_project / "go.mod").write_text("module example.com/test")
        collector = ProjectInfoCollector(temp_project, {"go": "go"})
        commands = collector.collect_test_commands()
        assert "go test ./..." in commands

    # ... (moved tests removed) ...

    def test_collect_build_commands_from_pipeline_script(self, temp_project):
        """パイプラインスクリプトからのビルドコマンド収集テスト"""
        scripts_dir = temp_project / "scripts"
        scripts_dir.mkdir()
        pipeline_script = scripts_dir / "run_pipeline.sh"
        pipeline_script.write_text("""
#!/bin/bash
echo "Building project..."
make build
npm run build
python setup.py build
        """)

        collector = ProjectInfoCollector(temp_project)
        commands = collector.build_collector.collect_build_commands()

        assert "make build" in commands
        assert "npm run build" in commands
        assert "python setup.py build" in commands

    def test_collect_build_commands_with_package_managers(self, temp_project):
        """パッケージマネージャ考慮のビルドコマンド収集テスト"""
        # Pythonプロジェクト
        collector = ProjectInfoCollector(temp_project, {"python": "uv"})
        commands = collector.build_collector.collect_build_commands()
        # uvプロジェクトでは特別なビルドコマンドは追加されない

        # JavaScriptプロジェクト
        collector = ProjectInfoCollector(temp_project, {"javascript": "pnpm"})
        package_json = temp_project / "package.json"
        package_json.write_text('{"scripts": {"build": "webpack"}}')
        commands = collector.build_collector.collect_build_commands()
        assert "pnpm run build" in commands

        # Goプロジェクト
        collector = ProjectInfoCollector(temp_project, {"go": "go"})
        commands = collector.build_collector.collect_build_commands()
        assert "go build" in commands

    def test_collect_build_commands_from_makefile(self, temp_project):
        """Makefileからのビルドコマンド収集テスト"""
        makefile = temp_project / "Makefile"
        makefile.write_text("""
.PHONY: build test clean

build:
\t@echo "Building..."
\tgcc main.c -o main
\tgo build -o bin/app .

test:
\t@echo "Testing..."
\tgo test ./...

clean:
\t@echo "Cleaning..."
\trm -rf bin/
        """)

        collector = ProjectInfoCollector(temp_project)
        commands = collector.build_collector.collect_build_commands()

        assert "gcc main.c -o main" in commands
        assert "go build -o bin/app ." in commands

    def test_collect_build_commands_from_package_json(self, temp_project):
        """package.jsonからのビルドコマンド収集テスト"""
        package_json = temp_project / "package.json"
        package_json.write_text("""
{
  "name": "test-project",
  "scripts": {
    "build": "webpack --mode production",
    "compile": "tsc",
    "package": "npm pack"
  }
}
        """)

        collector = ProjectInfoCollector(temp_project)
        commands = collector.build_collector.collect_build_commands()

        assert "npm run build" in commands
        assert "npm run compile" in commands

    def test_collect_test_commands_from_makefile(self, temp_project):
        """Makefileからのテストコマンド収集テスト"""
        makefile = temp_project / "Makefile"
        makefile.write_text("""
test:
\tpytest tests/
\tgo test ./...
\tnpm test

integration-test:
\tdocker-compose up -d
\tpytest tests/integration/
""")

        collector = ProjectInfoCollector(temp_project)
        commands = collector.collect_test_commands()

        assert "pytest tests/" in commands
        assert "go test ./..." in commands
        assert "npm test" in commands
