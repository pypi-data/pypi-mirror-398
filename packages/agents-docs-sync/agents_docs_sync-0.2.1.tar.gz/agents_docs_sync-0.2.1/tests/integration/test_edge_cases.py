"""
エッジケースのテスト
異常な入力や特殊な状況に対するテスト
"""

from pathlib import Path

import pytest

from docgen.docgen import DocGen
from docgen.generators.agents_generator import AgentsGenerator
from docgen.generators.api_generator import APIGenerator
from docgen.generators.parsers.python_parser import PythonParser
from docgen.generators.readme_generator import ReadmeGenerator
from docgen.utils.llm import LLMClientFactory


class TestEdgeCases:
    """エッジケースのテスト"""

    def test_empty_project_root(self):
        """空のプロジェクトルートでのテスト"""
        with pytest.raises((ValueError, TypeError)):
            DocGen(project_root=Path(""), config_path=None)

    def test_nonexistent_project_root(self):
        """存在しないプロジェクトルートでのテスト"""
        nonexistent_path = Path("/definitely/does/not/exist")
        docgen = DocGen(project_root=nonexistent_path)
        # 存在しないパスでも初期化は成功するはず
        assert docgen.project_root == nonexistent_path

    def test_python_parser_with_malformed_ast(self, temp_project):
        """不正なASTを持つPythonファイルの解析テスト"""
        # 構文エラーのあるPythonファイル
        python_file = temp_project / "broken.py"
        python_file.write_text("""
def broken_function(
    return "incomplete"  # 構文エラー
""")

        parser = PythonParser(temp_project)
        apis = parser.parse_file(python_file)

        # 構文エラーの場合は空のリストが返される
        assert apis == []

    def test_python_parser_with_unicode_content(self, temp_project):
        """Unicode文字を含むPythonファイルの解析テスト"""
        python_file = temp_project / "unicode.py"
        python_file.write_text("""
def greet(name: str) -> str:
    '''こんにちは、{name}さん！

    これはUnicodeを含むdocstringです。
    '''
    return f"こんにちは、{name}！"
""")

        parser = PythonParser(temp_project)
        apis = parser.parse_file(python_file)

        assert len(apis) == 1
        api = apis[0]
        assert api.name == "greet"
        assert "こんにちは" in (api.docstring or "")

    def test_python_parser_with_very_long_docstring(self, temp_project):
        """非常に長いdocstringの解析テスト"""
        long_docstring = " ".join([f"line_{i}" for i in range(1000)])

        python_file = temp_project / "long_doc.py"
        python_file.write_text(f'''
def long_function() -> None:
    """{long_docstring}"""
    pass
''')

        parser = PythonParser(temp_project)
        apis = parser.parse_file(python_file)

        assert len(apis) == 1
        api = apis[0]
        assert api.docstring is not None
        assert len(api.docstring) > 1000

    def test_agents_generator_with_invalid_config(self, temp_project):
        """無効な設定でのAgentsGeneratorテスト"""
        invalid_config = {
            "agents": {
                "llm_mode": "invalid_mode"  # 無効なモード
            }
        }

        generator = AgentsGenerator(temp_project, ["python"], invalid_config)
        result = generator.generate()

        # 無効な設定でも基本的なドキュメントは生成されるはず
        assert isinstance(result, bool)

    def test_api_generator_with_empty_languages(self, temp_project):
        """空の言語リストでのAPIGeneratorテスト"""
        config = {"output": {"api_doc": "api.md"}}

        generator = APIGenerator(temp_project, [], config)
        result = generator.generate()

        # 言語がない場合は空のAPIドキュメントが生成されるはず
        assert result is True
        assert (temp_project / "api.md").exists()

    def test_readme_generator_with_readonly_filesystem(self, temp_project, monkeypatch):
        """読み取り専用ファイルシステムでのReadmeGeneratorテスト"""
        # 書き込み権限をモックしてエラーをシミュレート

        def mock_open(*args, **kwargs):
            raise PermissionError("Read-only filesystem")

        monkeypatch.setattr("builtins.open", mock_open)

        config = {"output": {"readme": "README.md"}}
        generator = ReadmeGenerator(temp_project, ["python"], config)
        result = generator.generate()

        # 書き込みエラーが発生してもFalseが返される
        assert result is False

    def test_docgen_with_circular_imports(self, temp_project):
        """循環インポートのあるプロジェクトのテスト"""
        # 循環インポートのあるPythonファイル
        (temp_project / "a.py").write_text("""
from b import B
class A:
    def __init__(self):
        self.b = B()
""")

        (temp_project / "b.py").write_text("""
from a import A
class B:
    def __init__(self):
        self.a = A()
""")

        docgen = DocGen(project_root=temp_project)
        result = docgen.generate_documents()

        # 循環インポートがあっても基本的な処理は成功するはず
        assert isinstance(result, bool)

    def test_docgen_with_very_deep_directory_structure(self, temp_project):
        """非常に深いディレクトリ構造のテスト"""
        # 深いディレクトリ構造を作成
        deep_path = temp_project
        for i in range(20):  # 20階層の深さ
            deep_path = deep_path / f"level_{i}"
            deep_path.mkdir()

        # 最深部にPythonファイルを作成
        (deep_path / "deep.py").write_text("""
def deep_function():
    '''Function in deep directory'''
    return "deep"
""")

        docgen = DocGen(project_root=temp_project)
        result = docgen.generate_documents()

        # 深い構造でも正常に動作するはず
        assert isinstance(result, bool)

    def test_docgen_with_special_characters_in_paths(self, temp_project):
        """パスに特殊文字を含む場合のテスト"""
        # 特殊文字を含むディレクトリ名
        special_dir = temp_project / "special-dir_@#$%^&()"
        special_dir.mkdir()

        (special_dir / "special.py").write_text("""
def special_function():
    '''Function with special characters in path'''
    return "special"
""")

        docgen = DocGen(project_root=temp_project)
        result = docgen.generate_documents()

        # 特殊文字があっても正常に動作するはず
        assert isinstance(result, bool)

    def test_docgen_with_symlink_loops(self, temp_project):
        """シンボリックリンクのループがある場合のテスト"""
        # シンボリックリンクのループを作成（可能であれば）
        try:
            dir1 = temp_project / "dir1"
            dir2 = temp_project / "dir2"
            dir1.mkdir()
            dir2.mkdir()

            # 相互にリンク（プラットフォームによっては失敗する）
            (dir1 / "link_to_dir2").symlink_to(dir2)
            (dir2 / "link_to_dir1").symlink_to(dir1)
        except OSError:
            # シンボリックリンクがサポートされていない場合はスキップ
            pytest.skip("Symlinks not supported on this platform")

        docgen = DocGen(project_root=temp_project)
        result = docgen.generate_documents()

        # シンボリックリンクのループがあってもクラッシュしない
        assert isinstance(result, bool)

    def test_python_parser_with_binary_file_extension(self, temp_project):
        """.pycファイルなどのバイナリ拡張子のテスト"""
        # Pythonバイトコードファイル（実際にはテキスト）
        pyc_file = temp_project / "module.pyc"
        pyc_file.write_text("fake bytecode")

        parser = PythonParser(temp_project)
        apis = parser.parse_file(pyc_file)

        # .pycファイルは解析できないので空のリスト
        assert apis == []

    def test_agents_generator_with_very_long_custom_instructions(self, temp_project):
        """非常に長いカスタム指示のテスト"""
        long_instructions = "Custom instruction: " + "x" * 10000

        config = {
            "output": {"agents_doc": "AGENTS.md"},
            "agents": {"llm_mode": "api", "custom_instructions": long_instructions},
        }

        generator = AgentsGenerator(temp_project, ["python"], config)
        result = generator.generate()

        # 長い指示でも処理できるはず
        assert isinstance(result, bool)

    def test_api_generator_with_mixed_file_types(self, temp_project):
        """混在したファイルタイプのテスト"""
        # さまざまなファイルを作成
        (temp_project / "script.py").write_text("""
def hello():
    '''Hello function'''
    print('python')
""")
        (temp_project / "script.js").write_text("""
function hello() {
    console.log('js');
}
""")
        (temp_project / "readme.txt").write_text("text file")
        (temp_project / "binary.bin").write_text("fake binary")

        config = {"output": {"api_doc": "api.md"}}
        generator = APIGenerator(temp_project, ["python", "javascript"], config)
        result = generator.generate()

        assert result is True

        content = (temp_project / "api.md").read_text(encoding="utf-8")
        # PythonとJavaScriptのAPIのみが含まれるはず
        assert "script.py" in content or "script.js" in content

    def test_llm_client_factory_with_invalid_config(self):
        """無効なLLM設定でのテスト"""
        invalid_config = {"api": {"provider": "nonexistent"}}
        client = LLMClientFactory.create_client(invalid_config, "api")
        assert client is None

    def test_llm_client_factory_fallback(self):
        """LLMクライアントのフォールバックテスト"""
        config = {"api": {"provider": "openai"}, "local": {"provider": "ollama"}}
        # 実際のLLMがないのでNoneが返されるが、エラーは発生しない
        client = LLMClientFactory.create_client_with_fallback(config, "api")
        # ライブラリがインストールされていない場合None
        assert client is None or hasattr(client, "generate")

    def test_agents_generator_with_llm_failure(self, temp_project):
        """LLM失敗時のAgentsGeneratorテスト"""
        config = {
            "output": {"agents_doc": "AGENTS.md"},
            "agents": {"llm_mode": "api", "api": {"provider": "invalid"}},
        }
        generator = AgentsGenerator(temp_project, ["python"], config)
        result = generator.generate()
        # LLMが失敗しても基本的なドキュメントは生成されるはず
        assert isinstance(result, bool)

    def test_readme_generator_with_llm_failure(self, temp_project):
        """LLM失敗時のReadmeGeneratorテスト"""
        config = {
            "output": {"readme": "README.md"},
            "readme": {"llm_mode": "api", "api": {"provider": "invalid"}},
        }
        generator = ReadmeGenerator(temp_project, ["python"], config)
        result = generator.generate()
        # LLMが失敗しても基本的なREADMEは生成されるはず
        assert isinstance(result, bool)
