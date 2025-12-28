"""Embedderのテスト"""

import numpy as np
import pytest

from docgen.rag.embedder import Embedder


class TestEmbedder:
    """Embedderクラスのテスト"""

    @pytest.fixture
    def embedder(self):
        """テスト用のEmbedderインスタンス"""
        config = {"embedding": {"model": "all-MiniLM-L6-v2", "device": "cpu"}}
        return Embedder(config)

    def test_embedder_initialization(self, embedder):
        """Embedderが正しく初期化されることを確認"""
        assert embedder.model_name == "all-MiniLM-L6-v2"
        assert embedder.device == "cpu"

    def test_embedding_dim(self, embedder):
        """埋め込み次元が正しく取得できることを確認"""
        dim = embedder.embedding_dim
        assert isinstance(dim, int)
        assert dim > 0
        # all-MiniLM-L6-v2は384次元
        assert dim == 384

    def test_embed_text(self, embedder):
        """テキストの埋め込みが生成できることを確認"""
        text = "This is a test sentence."
        embedding = embedder.embed_text(text)

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (embedder.embedding_dim,)
        assert embedding.dtype == np.float32 or embedding.dtype == np.float64

    def test_embed_text_different_inputs(self, embedder):
        """異なるテキストは異なる埋め込みを生成することを確認"""
        text1 = "This is a test."
        text2 = "This is completely different."

        emb1 = embedder.embed_text(text1)
        emb2 = embedder.embed_text(text2)

        # 埋め込みが異なることを確認（コサイン類似度が1でない）
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        assert similarity < 0.99  # ほぼ同じでないことを確認

    def test_embed_text_same_input(self, embedder):
        """同じテキストは同じ埋め込みを生成することを確認"""
        text = "This is a test sentence."

        emb1 = embedder.embed_text(text)
        emb2 = embedder.embed_text(text)

        # 完全に同じ埋め込みになる（キャッシュの可能性も）
        np.testing.assert_array_almost_equal(emb1, emb2)

    def test_embed_batch(self, embedder):
        """バッチ処理で複数のテキストを埋め込めることを確認"""
        texts = [
            "First sentence.",
            "Second sentence.",
            "Third sentence.",
        ]

        embeddings = embedder.embed_batch(texts, batch_size=2)

        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (len(texts), embedder.embedding_dim)

    def test_embed_batch_empty(self, embedder):
        """空のリストを渡してもエラーにならないことを確認"""
        texts = []
        embeddings = embedder.embed_batch(texts)

        assert isinstance(embeddings, np.ndarray)
        assert len(embeddings) == 0

    def test_cache_key_generation(self, embedder):
        """キャッシュキーが正しく生成されることを確認"""
        text1 = "test"
        text2 = "test"
        text3 = "different"

        key1 = embedder._get_cache_key(text1)
        key2 = embedder._get_cache_key(text2)
        key3 = embedder._get_cache_key(text3)

        assert key1 == key2  # 同じテキストは同じキー
        assert key1 != key3  # 異なるテキストは異なるキー
        assert key1.startswith("emb_")  # キーのプレフィックスを確認
