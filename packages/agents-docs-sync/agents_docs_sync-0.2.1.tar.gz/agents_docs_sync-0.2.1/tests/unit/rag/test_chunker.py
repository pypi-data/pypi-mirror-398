"""CodeChunkerのテスト"""

from pathlib import Path

from docgen.rag.chunker import CodeChunker


class TestCodeChunker:
    """CodeChunkerクラスのテスト"""

    def test_should_process_file_excludes_test_files(self):
        """テストファイルが除外されることを確認"""
        chunker = CodeChunker()

        assert not chunker.should_process_file(Path("tests/test_foo.py"))
        assert not chunker.should_process_file(Path("__pycache__/foo.pyc"))

    def test_should_process_file_excludes_secrets(self):
        """機密ファイルが除外されることを確認"""
        chunker = CodeChunker()

        assert not chunker.should_process_file(Path(".env"))
        assert not chunker.should_process_file(Path("secrets/api_key.txt"))
        assert not chunker.should_process_file(Path("config_SECRET.yaml"))

    def test_should_process_file_includes_source_files(self):
        """ソースファイルが処理対象に含まれることを確認"""
        chunker = CodeChunker()

        assert chunker.should_process_file(Path("src/main.py"))
        assert chunker.should_process_file(Path("config.toml"))

    def test_should_process_file_excludes_configured_files(self):
        """設定で除外されたファイルが除外されることを確認"""
        config = {"exclude_files": ["README.md", "AGENTS.md"]}
        chunker = CodeChunker(config)

        assert not chunker.should_process_file(Path("README.md"))
        assert not chunker.should_process_file(Path("AGENTS.md"))
        assert chunker.should_process_file(Path("src/main.py"))  # 除外されていないファイルはOK

    def test_chunk_python_file(self, tmp_path):
        """Pythonファイルが関数/クラス単位でチャンクされることを確認"""
        # テストファイル作成
        test_file = tmp_path / "sample.py"
        test_file.write_text("""
def foo():
    '''Foo function'''
    pass

def bar():
    '''Bar function'''
    pass

class MyClass:
    '''My class'''
    def method(self):
        pass
""")

        chunker = CodeChunker()
        chunks = chunker.chunk_file(test_file, tmp_path)

        # 2つの関数と1つのクラスがチャンクされる
        assert len(chunks) >= 3

        # チャンクの構造を確認
        for chunk in chunks:
            assert "file" in chunk
            assert "type" in chunk
            assert "name" in chunk
            assert "text" in chunk
            assert "start_line" in chunk
            assert "end_line" in chunk
            assert "hash" in chunk

        # 関数名の確認
        names = [chunk["name"] for chunk in chunks]
        assert "foo" in names
        assert "bar" in names
        assert "MyClass" in names

    def test_chunk_markdown_file(self, tmp_path):
        """Markdownファイルがヘッダ単位でチャンクされることを確認"""
        test_file = tmp_path / "sample.md"
        test_file.write_text("""
# Header 1
Content 1

## Header 2
Content 2

### Header 3
Content 3
""")

        chunker = CodeChunker()
        chunks = chunker.chunk_file(test_file, tmp_path)

        assert len(chunks) >= 3

        # ヘッダ名の確認
        names = [chunk["name"] for chunk in chunks]
        assert any("Header 1" in name for name in names)
        assert any("Header 2" in name for name in names)

    def test_chunk_yaml_file(self, tmp_path):
        """YAMLファイルがセクション単位でチャンクされることを確認"""
        test_file = tmp_path / "sample.yaml"
        test_file.write_text("""
section1:
  key1: value1
  key2: value2

section2:
  key3: value3
""")

        chunker = CodeChunker()
        chunks = chunker.chunk_file(test_file, tmp_path)

        assert len(chunks) >= 2

        # セクション名の確認
        names = [chunk["name"] for chunk in chunks]
        assert "section1" in names
        assert "section2" in names

    def test_chunk_toml_file(self, tmp_path):
        """TOMLファイルがセクション単位でチャンクされることを確認"""
        test_file = tmp_path / "sample.toml"
        test_file.write_text("""
[section1]
key1 = "value1"

[section2]
key2 = "value2"
""")

        chunker = CodeChunker()
        chunks = chunker.chunk_file(test_file, tmp_path)

        assert len(chunks) >= 2

    def test_chunk_codebase_integration(self, tmp_path):
        """プロジェクト全体のチャンク化が動作することを確認"""
        # 簡単なプロジェクト構造を作成
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("def main(): pass")
        (tmp_path / "config.toml").write_text(
            "key: value"
        )  # README.mdは除外されるのでconfig.tomlを使用

        chunker = CodeChunker()
        chunks = chunker.chunk_codebase(tmp_path)

        # 少なくとも2つのチャンクが生成される
        assert len(chunks) >= 2

        # ファイルパスが相対パスになっている
        for chunk in chunks:
            assert not Path(chunk["file"]).is_absolute()
