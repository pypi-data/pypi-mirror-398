"""VectorIndexerのテスト"""

import numpy as np
import pytest

from docgen.rag.indexer import VectorIndexer


class TestVectorIndexer:
    """VectorIndexerクラスのテスト"""

    @pytest.fixture
    def sample_embeddings(self):
        """テスト用の埋め込みベクトル"""
        np.random.seed(42)
        return np.random.rand(10, 384).astype("float32")

    @pytest.fixture
    def sample_metadata(self):
        """テスト用のメタデータ"""
        return [
            {
                "file": f"test{i}.py",
                "type": "FunctionDef",
                "name": f"func{i}",
                "text": f"def func{i}(): pass",
                "start_line": i,
                "end_line": i + 1,
                "hash": f"hash{i}",
            }
            for i in range(10)
        ]

    @pytest.fixture
    def indexer(self, tmp_path):
        """テスト用のVectorIndexerインスタンス"""
        config = {"index": {"type": "hnswlib", "ef_construction": 200, "M": 16}}
        return VectorIndexer(index_dir=tmp_path / "index", embedding_dim=384, config=config)

    def test_indexer_initialization(self, indexer, tmp_path):
        """VectorIndexerが正しく初期化されることを確認"""
        assert indexer.embedding_dim == 384
        assert indexer.index_type == "hnswlib"
        assert (tmp_path / "index").exists()

    def test_build_index(self, indexer, sample_embeddings, sample_metadata):
        """インデックスの構築が正しく動作することを確認"""
        indexer.build(sample_embeddings, sample_metadata)

        assert indexer._index is not None
        assert len(indexer._metadata) == len(sample_metadata)

    def test_build_index_dimension_mismatch(self, indexer, sample_metadata):
        """埋め込み次元が一致しない場合にエラーになることを確認"""
        wrong_embeddings = np.random.rand(10, 256).astype("float32")

        with pytest.raises(ValueError, match="Expected embedding dimension"):
            indexer.build(wrong_embeddings, sample_metadata)

    def test_build_index_length_mismatch(self, indexer, sample_embeddings):
        """埋め込みとメタデータの長さが一致しない場合にエラーになることを確認"""
        wrong_metadata = [{"file": "test.py"}] * 5  # 10個必要だが5個しかない

        with pytest.raises(ValueError, match="must have the same length"):
            indexer.build(sample_embeddings, wrong_metadata)

    def test_save_and_load_index(self, indexer, sample_embeddings, sample_metadata, tmp_path):
        """インデックスの保存と読み込みが正しく動作することを確認"""
        # インデックスを構築して保存
        indexer.build(sample_embeddings, sample_metadata)
        indexer.save()

        # ファイルが存在することを確認
        index_dir = tmp_path / "index"
        assert (index_dir / "hnswlib.idx").exists()
        assert (index_dir / "meta.json").exists()

        # 新しいインスタンスで読み込み
        config = {"index": {"type": "hnswlib"}}
        indexer2 = VectorIndexer(index_dir=index_dir, embedding_dim=384, config=config)
        indexer2.load()

        assert len(indexer2._metadata) == len(sample_metadata)
        assert indexer2._index is not None

    def test_search(self, indexer, sample_embeddings, sample_metadata):
        """検索が正しく動作することを確認"""
        # インデックス構築
        indexer.build(sample_embeddings, sample_metadata)

        # 最初の埋め込みで検索
        query_embedding = sample_embeddings[0]
        results = indexer.search(query_embedding, k=3)

        assert len(results) <= 3

        # 結果の形式を確認
        for metadata, score in results:
            assert isinstance(metadata, dict)
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0

    def test_search_returns_closest_match(self, indexer, sample_embeddings, sample_metadata):
        """検索が最も近い結果を返すことを確認"""
        indexer.build(sample_embeddings, sample_metadata)

        # 最初の埋め込みで検索（自分自身が最も近いはず）
        query_embedding = sample_embeddings[0]
        results = indexer.search(query_embedding, k=1)

        assert len(results) == 1
        metadata, score = results[0]

        # スコアがほぼ1.0（自分自身との類似度）
        assert score > 0.99

    def test_incremental_update(self, indexer, sample_embeddings, sample_metadata):
        """増分更新が正しく動作することを確認"""
        # 最初のインデックスを構築
        initial_embeddings = sample_embeddings[:5]
        initial_metadata = sample_metadata[:5]
        indexer.build(initial_embeddings, initial_metadata)

        assert len(indexer._metadata) == 5

        # 新しいデータを追加
        new_embeddings = sample_embeddings[5:7]
        new_metadata = sample_metadata[5:7]
        indexer.incremental_update(new_embeddings, new_metadata)

        assert len(indexer._metadata) == 7

    def test_save_metadata_structure(self, indexer, sample_embeddings, sample_metadata, tmp_path):
        """保存されるメタデータの構造が正しいことを確認"""
        import json

        indexer.build(sample_embeddings, sample_metadata)
        indexer.save()

        # メタデータファイルを読み込み
        meta_path = tmp_path / "index" / "meta.json"
        with open(meta_path) as f:
            meta = json.load(f)

        assert "chunk_count" in meta
        assert "embedding_dim" in meta
        assert "index_type" in meta
        assert "chunks" in meta

        assert meta["chunk_count"] == len(sample_metadata)
        assert meta["embedding_dim"] == 384
        assert meta["index_type"] == "hnswlib"
