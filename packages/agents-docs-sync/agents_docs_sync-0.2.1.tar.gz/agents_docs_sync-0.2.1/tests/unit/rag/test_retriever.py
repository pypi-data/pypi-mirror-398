"""DocumentRetrieverのテスト"""

from unittest.mock import Mock, patch

import pytest

from docgen.rag.retriever import DocumentRetriever


class TestDocumentRetriever:
    """DocumentRetrieverクラスのテスト"""

    @pytest.fixture
    def config(self):
        """テスト用の設定"""
        return {
            "rag": {
                "enabled": True,
                "embedding": {"model": "all-MiniLM-L6-v2", "device": "cpu"},
                "index": {"type": "hnswlib", "ef_construction": 200, "M": 16},
                "retrieval": {"top_k": 6, "score_threshold": 0.3},
            }
        }

    @pytest.fixture
    def sample_chunks(self):
        """テスト用のチャンクデータ"""
        return [
            {
                "file": "test1.py",
                "type": "FunctionDef",
                "name": "foo",
                "text": "def foo(): pass",
                "start_line": 1,
                "end_line": 2,
                "hash": "hash1",
                "similarity_score": 0.9,
            },
            {
                "file": "test2.py",
                "type": "FunctionDef",
                "name": "bar",
                "text": "def bar(): pass",
                "start_line": 5,
                "end_line": 6,
                "hash": "hash2",
                "similarity_score": 0.7,
            },
        ]

    def test_retriever_initialization(self, config, tmp_path):
        """DocumentRetrieverが正しく初期化されることを確認"""
        retriever = DocumentRetriever(config, tmp_path)

        assert retriever.config == config
        assert retriever.rag_config == config["rag"]
        assert retriever.default_top_k == 6
        assert retriever.score_threshold == 0.3

    def test_format_context(self, config, sample_chunks, tmp_path):
        """コンテキストのフォーマットが正しく動作することを確認"""
        retriever = DocumentRetriever(config, tmp_path)
        formatted = retriever.format_context(sample_chunks)

        assert isinstance(formatted, str)
        assert "test1.py:1-2" in formatted
        assert "test2.py:5-6" in formatted
        assert "def foo(): pass" in formatted
        assert "def bar(): pass" in formatted
        assert "score: 0.9" in formatted or "score: 0.900" in formatted

    def test_format_context_empty(self, config, tmp_path):
        """空のチャンクリストを渡した場合の動作を確認"""
        retriever = DocumentRetriever(config, tmp_path)
        formatted = retriever.format_context([])

        assert formatted == ""

    @patch("docgen.rag.retriever.Embedder")
    @patch("docgen.rag.retriever.VectorIndexer")
    def test_retrieve_filters_by_threshold(
        self, mock_indexer_class, mock_embedder_class, config, tmp_path
    ):
        """スコア閾値でフィルタリングされることを確認"""
        # モックの設定
        mock_embedder = Mock()
        mock_embedder.embed_text.return_value = [0.1] * 384
        mock_embedder.embedding_dim = 384
        mock_embedder_class.return_value = mock_embedder

        mock_indexer = Mock()
        # スコアが異なる結果を返す（閾値0.3を基準）
        # hashを含めることでsimilarity_scoreが追加される
        mock_indexer.search.return_value = [
            ({"file": "test1.py", "name": "high_score", "hash": "hash1"}, 0.8),  # 閾値以上
            ({"file": "test2.py", "name": "medium_score", "hash": "hash2"}, 0.5),  # 閾値以上
            ({"file": "test3.py", "name": "low_score", "hash": "hash3"}, 0.2),  # 閾値未満
        ]
        mock_indexer_class.return_value = mock_indexer

        retriever = DocumentRetriever(config, tmp_path)
        retriever._indexer = mock_indexer
        retriever._embedder = mock_embedder

        results = retriever.retrieve("test query", top_k=10)

        # 閾値0.3以上のものだけが返される
        assert len(results) == 2
        assert all(chunk.get("similarity_score", 0) >= 0.3 for chunk in results)

    def test_embedder_lazy_loading(self, config, tmp_path):
        """Embedderが遅延ロードされることを確認"""
        retriever = DocumentRetriever(config, tmp_path)

        # 初期状態では None
        assert retriever._embedder is None

        # アクセス時にロードされる（ImportErrorになる可能性があるのでtry-except）
        try:
            _ = retriever.embedder
            assert retriever._embedder is not None
        except (ImportError, FileNotFoundError):
            # RAG依存関係がインストールされていない場合はスキップ
            pytest.skip("RAG dependencies not installed")

    def test_indexer_lazy_loading(self, config, tmp_path):
        """VectorIndexerが遅延ロードされることを確認"""
        retriever = DocumentRetriever(config, tmp_path)

        # 初期状態では None
        assert retriever._indexer is None

        # アクセス時にロードを試みる（インデックスがない場合はエラー）
        with pytest.raises(FileNotFoundError):
            _ = retriever.indexer
