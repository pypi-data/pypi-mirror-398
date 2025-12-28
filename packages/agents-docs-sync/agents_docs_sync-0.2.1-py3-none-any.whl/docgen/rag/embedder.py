"""テキスト埋め込み生成モジュール

sentence-transformersを使用してテキストの埋め込みベクトルを生成します。
"""

import hashlib
from logging import Logger
from pathlib import Path
from typing import Any

import numpy as np

from ..utils.logger import get_logger


class Embedder:
    """テキスト埋め込み生成クラス"""

    def __init__(self, config: dict[str, Any] | None = None, logger: Logger | None = None):
        """
        初期化

        Args:
            config: RAG設定（config.toml の rag セクション）
            logger: ロガーインスタンス（Noneの場合は新規作成）
        """
        self.config = config or {}
        embedding_config = self.config.get("embedding", {})

        self.model_name = embedding_config.get("model", "all-MiniLM-L6-v2")
        self.device = embedding_config.get("device", "cpu")
        self.logger = logger or get_logger(__name__)

        self._model = None  # Lazy loading

        # キャッシュディレクトリ（プロジェクトローカルではなくユーザーホーム）
        self.cache_dir = Path.home() / ".cache" / "agents-docs-sync" / "embeddings"

    @property
    def model(self):
        """埋め込みモデルをLazy load"""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self.logger.info(f"Loading embedding model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name, device=self.device)
                self.logger.info(f"Model loaded successfully (dimension: {self.embedding_dim})")
            except ImportError as e:
                raise ImportError(
                    "sentence-transformers is not installed. "
                    "Install RAG dependencies with: uv sync --extra rag"
                ) from e

        return self._model

    @property
    def embedding_dim(self) -> int:
        """埋め込みベクトルの次元数"""
        return self.model.get_sentence_embedding_dimension()

    def embed_text(self, text: str) -> np.ndarray:
        """
        テキストを埋め込みベクトルに変換

        Args:
            text: 入力テキスト

        Returns:
            埋め込みベクトル（numpy配列）
        """
        # キャッシュキーを生成
        cache_key = self._get_cache_key(text)

        # キャッシュから取得を試みる
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        # 埋め込み生成
        embedding = self.model.encode(text, convert_to_numpy=True)

        # キャッシュに保存
        self._save_to_cache(cache_key, embedding)

        return embedding

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """
        複数のテキストをバッチ処理で埋め込み（キャッシュ対応）

        Args:
            texts: 入力テキストのリスト
            batch_size: バッチサイズ

        Returns:
            埋め込みベクトルの配列（shape: [len(texts), embedding_dim]）
        """
        self.logger.info(f"Embedding {len(texts)} texts with batch size {batch_size}")

        # キャッシュをチェック
        embeddings_dict: dict[int, np.ndarray] = {}
        texts_to_embed = []
        indices_to_embed = []

        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                embeddings_dict[i] = cached
            else:
                texts_to_embed.append(text)
                indices_to_embed.append(i)

        # 未キャッシュのテキストのみバッチ処理
        if texts_to_embed:
            self.logger.debug(
                f"Cache hit: {len(embeddings_dict)}/{len(texts)}, "
                f"miss: {len(texts_to_embed)}/{len(texts)}"
            )
            new_embeddings = self.model.encode(
                texts_to_embed,
                batch_size=batch_size,
                show_progress_bar=len(texts_to_embed) > batch_size,
                convert_to_numpy=True,
            )

            # キャッシュに保存
            for text, embedding in zip(texts_to_embed, new_embeddings, strict=True):
                cache_key = self._get_cache_key(text)
                self._save_to_cache(cache_key, embedding)

            # インデックスと埋め込みをマッピング
            for idx, emb in zip(indices_to_embed, new_embeddings, strict=True):
                embeddings_dict[idx] = emb
        else:
            self.logger.debug(f"All {len(texts)} texts found in cache")

        # インデックス順にソートして返す
        sorted_indices = sorted(embeddings_dict.keys())
        embeddings_list = [embeddings_dict[i] for i in sorted_indices]
        return np.array(embeddings_list)

    def _get_cache_key(self, text: str) -> str:
        """テキストからキャッシュキーを生成"""
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        return f"emb_{self.model_name}_{text_hash}"

    def _get_from_cache(self, cache_key: str) -> np.ndarray | None:
        """キャッシュから埋め込みを取得"""
        try:
            cache_path = self.cache_dir / f"{cache_key}.npy"
            if cache_path.exists():
                return np.load(cache_path)
        except Exception as e:
            self.logger.debug(f"Cache read failed: {e}")

        return None

    def _save_to_cache(self, cache_key: str, embedding: np.ndarray):
        """埋め込みをキャッシュに保存"""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            cache_path = self.cache_dir / f"{cache_key}.npy"
            np.save(cache_path, embedding)
        except Exception as e:
            self.logger.debug(f"Cache write failed: {e}")
