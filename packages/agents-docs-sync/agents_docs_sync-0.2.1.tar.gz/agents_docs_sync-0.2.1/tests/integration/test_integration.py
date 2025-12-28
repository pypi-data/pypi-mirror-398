"""
統合テスト
エンドツーエンドの機能をテスト
"""

from pathlib import Path

from docgen.docgen import DocGen


class TestIntegration:
    """統合テストクラス"""

    def test_full_pipeline_python_project(self, temp_project, caplog):
        """Pythonプロジェクトの完全なパイプラインテスト"""
        # Pythonプロジェクトファイルを作成
        (temp_project / "src").mkdir()
        (temp_project / "src" / "__init__.py").write_text("")
        (temp_project / "src" / "main.py").write_text("""
def hello_world(name: str) -> str:
    \"\"\"Say hello to world.

    Args:
        name: The name to greet

    Returns:
        A greeting message
    \"\"\"
    return f"Hello, {name}!"

class Calculator:
    \"\"\"A simple calculator class.\"\"\"

    def __init__(self, initial_value: int):
        \"\"\"Initialize calculator.

        Args:
            initial_value: Starting value
        \"\"\"
        self.value = initial_value

    def add(self, a: int, b: int) -> int:
        \"\"\"Add two numbers.

        Args:
            a: First number
            b: Second number

        Returns:
            The sum of a and b
        \"\"\"
        return a + b
""")

        # 設定ファイルを作成
        (temp_project / "docgen").mkdir(exist_ok=True)
        (temp_project / "docgen" / "config.toml").write_text("""
[output]
api_doc = "docs/api.md"
readme = "README.md"
agents_doc = "AGENTS.md"

[generation]
preserve_manual_sections = true
""")

        # DocGenを実行
        docgen = DocGen(project_root=temp_project)
        result = docgen.generate_documents()

        assert result is True

        # 生成されたファイルを確認
        assert (temp_project / "docs" / "api.md").exists()
        assert (temp_project / "README.md").exists()
        assert (temp_project / "AGENTS.md").exists()

        # APIドキュメントの内容を確認
        api_content = (temp_project / "docs" / "api.md").read_text(encoding="utf-8")
        assert "# API ドキュメント" in api_content
        assert "hello_world" in api_content
        assert "Calculator" in api_content

        # READMEの内容を確認
        readme_content = (temp_project / "README.md").read_text(encoding="utf-8")
        assert "#" in readme_content  # プロジェクト名が含まれていること

        # AGENTS.mdの内容を確認
        agents_content = (temp_project / "AGENTS.md").read_text(encoding="utf-8")
        assert "AGENTS ドキュメント" in agents_content

    def test_full_pipeline_javascript_project(self, temp_project):
        """JavaScriptプロジェクトの完全なパイプラインテスト"""
        # JavaScriptプロジェクトファイルを作成
        (temp_project / "src").mkdir()
        (temp_project / "src" / "main.js").write_text("""
/**
 * Say hello to world
 * @param {string} name - The name to greet
 * @returns {string} A greeting message
 */
function helloWorld(name) {
    return `Hello, ${name}!`;
}

/**
 * Calculator class
 */
class Calculator {
    /**
     * Add two numbers
     * @param {number} a - First number
     * @param {number} b - Second number
     * @returns {number} The sum of a and b
     */
    add(a, b) {
        return a + b;
    }
}
""")

        # package.jsonを作成
        (temp_project / "package.json").write_text('{"name": "test-project", "version": "1.0.0"}')

        # 設定ファイルを作成
        (temp_project / "docgen").mkdir(exist_ok=True)
        (temp_project / "docgen" / "config.toml").write_text("""
[output]
api_doc = "docs/api.md"
readme = "README.md"
agents_doc = "AGENTS.md"
""")

        # DocGenを実行
        docgen = DocGen(project_root=temp_project)
        result = docgen.generate_documents()

        assert result is True

        # 生成されたファイルを確認
        assert (temp_project / "docs" / "api.md").exists()
        assert (temp_project / "README.md").exists()
        assert (temp_project / "AGENTS.md").exists()

        # APIドキュメントの内容を確認
        api_content = (temp_project / "docs" / "api.md").read_text(encoding="utf-8")
        assert "# API ドキュメント" in api_content
        assert "helloWorld" in api_content
        assert "Calculator" in api_content

    def test_detect_only_mode(self, temp_project, caplog):
        """言語検出のみモードのテスト"""
        # 複数の言語のファイルを作成
        (temp_project / "main.py").write_text('print("Python")')
        (temp_project / "main.js").write_text('console.log("JavaScript")')
        (temp_project / "main.go").write_text(
            'package main\n\nimport "fmt"\n\nfunc main() {\n\tfmt.Println("Go")\n}'
        )

        docgen = DocGen(project_root=temp_project)

        # 言語検出を実行
        languages = docgen.detect_languages()

        # 検出された言語を確認
        lang_names = [lang.name for lang in languages]
        assert "python" in lang_names
        assert "javascript" in lang_names
        assert "go" in lang_names

        # ログを確認
        assert "✓ 検出: python" in caplog.text
        assert "✓ 検出: javascript" in caplog.text
        assert "✓ 検出: go" in caplog.text

    def test_config_file_handling(self, temp_project):
        """設定ファイルハンドリングのテスト"""
        # 設定ファイルを作成
        config_dir = temp_project / "docgen"
        config_dir.mkdir(exist_ok=True)
        (config_dir / "config.toml").write_text("""
[output]
api_doc = "custom_api.md"
readme = "custom_readme.md"
agents_doc = "custom_agents.md"
""")

        # 簡単なPythonファイルを作成
        (temp_project / "main.py").write_text('print("test")')

        docgen = DocGen(project_root=temp_project)
        result = docgen.generate_documents()

        assert result is True

        # カスタムパスにファイルが生成されていることを確認
        assert (temp_project / "custom_api.md").exists()
        assert (temp_project / "custom_readme.md").exists()
        assert (temp_project / "custom_agents.md").exists()

    def test_error_handling(self, temp_project):
        """エラーハンドリングのテスト"""
        # 無効なPythonファイルを作成
        config_dir = temp_project / "docgen"
        config_dir.mkdir(exist_ok=True)
        (config_dir / "config.toml").write_text("""
[output]
api_doc = "docs/api.md"
readme = "README.md"
agents_doc = "AGENTS.md"
""")

        (temp_project / "invalid.py").write_text("def invalid_function(\n    # incomplete syntax")

        docgen = DocGen(project_root=temp_project)

        # エラーが発生しても処理が続行されることを確認
        docgen.generate_documents()

        # 少なくともREADMEは生成されるはず
        assert (temp_project / "README.md").exists()
