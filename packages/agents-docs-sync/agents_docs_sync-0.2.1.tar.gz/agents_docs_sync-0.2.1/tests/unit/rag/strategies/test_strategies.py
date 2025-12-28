"""
Tests for chunking strategies.
"""

import pytest

from docgen.rag.strategies.code_strategy import CodeChunkStrategy
from docgen.rag.strategies.markdown_strategy import MarkdownChunkStrategy
from docgen.rag.strategies.text_strategy import TextChunkStrategy


class TestStrategies:
    @pytest.fixture
    def project_root(self, tmp_path):
        return tmp_path

    def test_hash_text_consistency(self, project_root):
        """Test hash consistency across strategies."""
        strategy = TextChunkStrategy(project_root)
        text1 = "some text"
        text2 = "some text"
        text3 = "different text"

        hash1 = strategy._hash_text(text1)
        hash2 = strategy._hash_text(text2)
        hash3 = strategy._hash_text(text3)

        assert hash1 == hash2
        assert hash1 != hash3

    def test_code_strategy_python(self, project_root):
        strategy = CodeChunkStrategy(project_root)
        file_path = project_root / "test.py"
        content = """
def foo():
    pass

class Bar:
    def baz(self):
        pass
"""
        chunks = strategy.chunk(content, file_path)
        assert len(chunks) == 3
        assert chunks[0]["type"] == "FunctionDef"
        assert chunks[0]["name"] == "foo"
        assert chunks[1]["type"] == "ClassDef"
        assert chunks[1]["name"] == "Bar"
        assert chunks[2]["type"] == "FunctionDef"
        assert chunks[2]["name"] == "baz"

    def test_markdown_strategy(self, project_root):
        strategy = MarkdownChunkStrategy(project_root)
        file_path = project_root / "test.md"
        content = """
# Header 1
Content 1
## Header 2
Content 2
"""
        chunks = strategy.chunk(content, file_path)
        assert len(chunks) == 3
        assert chunks[0]["name"] == "Introduction"
        assert chunks[1]["name"] == "Header 1"
        assert chunks[2]["name"] == "Header 2"

    def test_text_strategy(self, project_root):
        strategy = TextChunkStrategy(project_root)
        file_path = project_root / "test.txt"
        content = "Line 1\nLine 2"
        chunks = strategy.chunk(content, file_path)
        assert len(chunks) == 1
        assert chunks[0]["type"] == "File"
        assert chunks[0]["text"] == content
