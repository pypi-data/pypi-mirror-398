"""ベクトルインデックス管理モジュール

hnswlibを使用してベクトルインデックスの構築、保存、読み込みを管理します。
"""

import json
from logging import Logger
from pathlib import Path
from typing import Any

import numpy as np

from ..utils.logger import get_logger


class VectorIndexer:
    """ベクトルインデックス管理クラス"""

    def __init__(
        self,
        index_dir: Path,
        embedding_dim: int = 384,
        config: dict[str, Any] | None = None,
        logger: Logger | None = None,
    ):
        """
        初期化

        Args:
            index_dir: インデックス保存ディレクトリ
            embedding_dim: 埋め込みベクトルの次元数
            config: RAG設定（config.toml の rag セクション）
            logger: ロガーインスタンス（Noneの場合は新規作成）
        """
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.embedding_dim = embedding_dim
        self.config = config or {}
        self.logger = logger or get_logger(__name__)

        index_config = self.config.get("index", {})
        self.index_type = index_config.get("type", "hnswlib")
        self.ef_construction = index_config.get("ef_construction", 200)
        self.M = index_config.get("M", 16)

        self._index: Any | None = None
        self._metadata: list[dict[str, Any]] = []

    def build(self, embeddings: np.ndarray, metadata: list[dict[str, Any]]):
        """
        インデックスを構築

        Args:
            embeddings: 埋め込みベクトルの配列（shape: [n_samples, embedding_dim]）
            metadata: 各埋め込みに対応するメタデータのリスト
        """
        if len(embeddings) != len(metadata):
            raise ValueError("embeddings and metadata must have the same length")

        if embeddings.shape[1] != self.embedding_dim:
            raise ValueError(
                f"Expected embedding dimension {self.embedding_dim}, got {embeddings.shape[1]}"
            )

        self.logger.info(f"Building {self.index_type} index with {len(embeddings)} vectors")

        if self.index_type == "hnswlib":
            self._build_hnswlib(embeddings)
        else:
            raise ValueError(f"Unsupported index type: {self.index_type}")

        self._metadata = metadata
        self.logger.info("Index built successfully")

    def _build_hnswlib(self, embeddings: np.ndarray):
        """hnswlibインデックスを構築"""
        try:
            import hnswlib
        except ImportError as e:
            raise ImportError(
                "hnswlib is not installed. Install RAG dependencies with: uv sync --extra rag"
            ) from e

        n_samples = len(embeddings)

        # インデックス作成
        self._index = hnswlib.Index(space="cosine", dim=self.embedding_dim)
        self._index.init_index(
            max_elements=n_samples,
            ef_construction=self.ef_construction,
            M=self.M,
        )

        # データ追加
        self._index.add_items(embeddings, np.arange(n_samples))

        # 検索パラメータ設定
        self._index.set_ef(50)  # 検索時の探索範囲

    def save(self):
        """インデックスとメタデータを保存"""
        if self._index is None:
            raise ValueError("Index has not been built yet")

        self.logger.info(f"Saving index to {self.index_dir}")

        # インデックスを保存
        index_path = self.index_dir / f"{self.index_type}.idx"
        if self.index_type == "hnswlib":
            self._index.save_index(str(index_path))

        # メタデータを保存
        meta_path = self.index_dir / "meta.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "chunk_count": len(self._metadata),
                    "embedding_dim": self.embedding_dim,
                    "index_type": self.index_type,
                    "chunks": self._metadata,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        self.logger.info(f"Saved index with {len(self._metadata)} chunks")

    def load(self):
        """インデックスとメタデータを読み込み"""
        self.logger.info(f"Loading index from {self.index_dir}")

        # メタデータを読み込み
        meta_path = self.index_dir / "meta.json"
        if not meta_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {meta_path}")

        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)

        self._metadata = meta["chunks"]
        self.embedding_dim = meta["embedding_dim"]
        self.index_type = meta.get("index_type", "hnswlib")

        # インデックスを読み込み
        index_path = self.index_dir / f"{self.index_type}.idx"
        if not index_path.exists():
            raise FileNotFoundError(f"Index file not found: {index_path}")

        if self.index_type == "hnswlib":
            self._load_hnswlib(index_path, meta["chunk_count"])

        self.logger.info(f"Loaded index with {len(self._metadata)} chunks")

    def _load_hnswlib(self, index_path: Path, max_elements: int):
        """hnswlibインデックスを読み込み"""
        try:
            import hnswlib
        except ImportError as e:
            raise ImportError(
                "hnswlib is not installed. Install RAG dependencies with: uv sync --extra rag"
            ) from e

        self._index = hnswlib.Index(space="cosine", dim=self.embedding_dim)
        if self._index is not None:
            self._index.load_index(str(index_path), max_elements=max_elements)
            self._index.set_ef(50)

    def search(self, query_embedding: np.ndarray, k: int = 6) -> list[tuple[dict[str, Any], float]]:
        """
        類似ベクトルを検索

        Args:
            query_embedding: クエリの埋め込みベクトル
            k: 取得する件数

        Returns:
            (メタデータ, スコア) のタプルのリスト
        """
        if self._index is None:
            raise ValueError("Index has not been loaded")

        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)

        # 検索実行
        labels, distances = self._index.knn_query(query_embedding, k=k)

        # 結果を整形
        results = []
        for idx, dist in zip(labels[0], distances[0], strict=True):
            if idx < len(self._metadata):
                # cosine距離をsimilarityスコアに変換 (1 - distance)
                similarity = 1.0 - dist
                results.append((self._metadata[idx], float(similarity)))

        return results

    def incremental_update(self, new_embeddings: np.ndarray, new_metadata: list[dict[str, Any]]):
        """
        インデックスに新しいデータを追加（増分更新）

        Args:
            new_embeddings: 新しい埋め込みベクトル
            new_metadata: 新しいメタデータ
        """
        if self._index is None:
            raise ValueError("Index has not been loaded")

        if len(new_embeddings) != len(new_metadata):
            raise ValueError("new_embeddings and new_metadata must have the same length")

        self.logger.info(f"Adding {len(new_embeddings)} new vectors to index")

        # 既存のチャンク数
        current_count = len(self._metadata)

        # 新しいIDを割り当ててデータを追加
        new_ids = np.arange(current_count, current_count + len(new_embeddings))

        # インデックスのサイズを拡張
        if self.index_type == "hnswlib":
            self._index.resize_index(current_count + len(new_embeddings))
            self._index.add_items(new_embeddings, new_ids)

        # メタデータを追加
        self._metadata.extend(new_metadata)

        self.logger.info(f"Index now contains {len(self._metadata)} chunks")
