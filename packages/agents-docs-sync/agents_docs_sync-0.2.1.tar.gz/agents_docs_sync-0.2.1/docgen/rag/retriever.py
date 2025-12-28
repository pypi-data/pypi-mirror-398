"""ドキュメント検索モジュール

ベクトルインデックスから類似チャンクを検索・取得します。
"""

from logging import Logger
from pathlib import Path
from typing import Any

from ..utils.logger import get_logger
from .embedder import Embedder
from .indexer import VectorIndexer


class DocumentRetriever:
    """ドキュメント検索クラス"""

    def __init__(
        self,
        config: dict[str, Any],
        project_root: Path | None = None,
        logger: Logger | None = None,
    ):
        """
        初期化

        Args:
            config: 設定辞書（config.toml全体）
            project_root: プロジェクトルート（指定しない場合は現在のディレクトリ）
            logger: ロガーインスタンス（Noneの場合は新規作成）
        """
        self.config = config
        self.rag_config = config.get("rag", {})
        self.project_root = project_root or Path.cwd()
        self.logger = logger or get_logger(__name__)

        # 検索設定
        retrieval_config = self.rag_config.get("retrieval", {})
        self.default_top_k = retrieval_config.get("top_k", 6)
        # デフォルト閾値を0.2に下げて、より多くの関連チャンクを取得
        self.score_threshold = retrieval_config.get("score_threshold", 0.2)

        # インデックスディレクトリ
        self.index_dir = self.project_root / "docgen" / "index"

        # コンポーネント（Lazy loading）
        self._embedder: Embedder | None = None
        self._indexer: VectorIndexer | None = None

    @property
    def embedder(self) -> Embedder:
        """Embedderインスタンスを取得（Lazy loading）"""
        if self._embedder is None:
            self._embedder = Embedder(self.rag_config, logger=self.logger)
        return self._embedder

    @property
    def indexer(self) -> VectorIndexer:
        """VectorIndexerインスタンスを取得（Lazy loading）"""
        if self._indexer is None:
            # Embedderから次元数を取得
            embedding_dim = self.embedder.embedding_dim

            self._indexer = VectorIndexer(
                index_dir=self.index_dir,
                embedding_dim=embedding_dim,
                config=self.rag_config,
                logger=self.logger,
            )

            # インデックスを読み込み
            try:
                self._indexer.load()
            except FileNotFoundError:
                self.logger.warning(
                    f"Index not found at {self.index_dir}. "
                    "Please build the index first with: "
                    "uv run python -m docgen.docgen --build-index"
                )
                raise

        return self._indexer

    def retrieve(self, query: str, top_k: int | None = None) -> list[dict[str, Any]]:
        """
        クエリに類似するチャンクを検索

        Args:
            query: 検索クエリ
            top_k: 取得する件数（Noneの場合はデフォルト値）

        Returns:
            チャンクのリスト（スコア付き）
        """
        k = top_k if top_k is not None else self.default_top_k

        self.logger.info(f"Retrieving top-{k} chunks for query: {query[:50]}...")

        # クエリを埋め込み
        query_embedding = self.embedder.embed_text(query)

        # 検索実行
        results = self.indexer.search(query_embedding, k=k)

        # スコアの統計情報をログ出力（デバッグ用）
        if results:
            scores = [score for _, score in results]
            max_score = max(scores)
            min_score = min(scores)
            avg_score = sum(scores) / len(scores)
            self.logger.debug(
                f"Score statistics: min={min_score:.3f}, max={max_score:.3f}, "
                f"avg={avg_score:.3f}, threshold={self.score_threshold}"
            )

        # スコア閾値でフィルタリング
        # ただし、top_kの結果が少ない場合は閾値を緩和
        filtered_results = [chunk for chunk, score in results if score >= self.score_threshold]

        # 閾値でフィルタリングした結果が少ない場合（top_kの30%未満）、
        # 閾値を下げて再フィルタリング（最低でもtop_kの50%は取得する）
        min_required = max(1, int(k * 0.3))  # 最低30%は取得

        if len(filtered_results) < min_required and results:
            # 動的に閾値を調整
            scores = [score for _, score in results]
            if scores:
                min_score = min(scores)
                max_score = max(scores)
                avg_score = sum(scores) / len(scores)

                # より積極的な閾値調整
                # 1. 平均スコアの70%を試す
                # 2. 最低スコアの90%を試す
                # 3. 最低でも0.15は維持
                candidate_thresholds = [
                    avg_score * 0.7,
                    min_score * 0.9,
                    0.15,
                ]
                adjusted_threshold = min(
                    self.score_threshold,
                    max(0.1, max(candidate_thresholds)),  # 最低0.1は維持
                )

                if adjusted_threshold < self.score_threshold:
                    self.logger.debug(
                        f"Adjusted threshold from {self.score_threshold:.3f} to {adjusted_threshold:.3f} "
                        f"(min={min_score:.3f}, max={max_score:.3f}, avg={avg_score:.3f}) "
                        f"to retrieve more relevant chunks"
                    )
                    filtered_results = [
                        chunk for chunk, score in results if score >= adjusted_threshold
                    ]

                    # それでも少ない場合は、さらに緩和（最低でもtop_kの30%は取得）
                    if len(filtered_results) < min_required:
                        # 最低スコアの少し上を閾値とする
                        final_threshold = max(0.1, min_score * 0.95)
                        if final_threshold < adjusted_threshold:
                            self.logger.debug(
                                f"Further adjusted threshold to {final_threshold:.3f} "
                                f"to meet minimum requirement ({min_required} chunks)"
                            )
                            filtered_results = [
                                chunk for chunk, score in results if score >= final_threshold
                            ]

        # スコアをメタデータに追加
        # resultsからfiltered_resultsに含まれるチャンクのスコアを追加
        # チャンクを識別するためにhashを使用
        filtered_hashes = {chunk.get("hash") for chunk in filtered_results if chunk.get("hash")}
        for chunk, score in results:
            if chunk.get("hash") in filtered_hashes:
                chunk["similarity_score"] = score

        self.logger.info(
            f"Retrieved {len(filtered_results)} chunks (threshold: {self.score_threshold:.3f}, "
            f"top_k: {k}, total results: {len(results)})"
        )

        return filtered_results

    def format_context(self, chunks: list[dict[str, Any]]) -> str:
        """
        チャンクをコンテキスト文字列にフォーマット

        Args:
            chunks: チャンクのリスト

        Returns:
            フォーマット済みのコンテキスト文字列
        """
        if not chunks:
            return ""

        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            # 出典情報
            source = f"{chunk['file']}:{chunk['start_line']}-{chunk['end_line']}"

            # スコア情報（あれば）
            score_info = ""
            if "similarity_score" in chunk:
                score_info = f" (score: {chunk['similarity_score']:.3f})"

            # チャンク情報
            context_parts.append(
                f"[{i}] {source}{score_info}\n"
                f"Type: {chunk['type']}, Name: {chunk['name']}\n"
                f"```\n{chunk['text']}\n```\n"
            )

        return "\n".join(context_parts)

    def retrieve_with_rerank(
        self, query: str, top_k: int = 6, rerank_k: int = 20
    ) -> list[dict[str, Any]]:
        """
        再ランキング付き検索（将来の拡張用）

        Args:
            query: 検索クエリ
            top_k: 最終的に取得する件数
            rerank_k: 初期検索で取得する件数（再ランク対象）

        Returns:
            再ランク済みのチャンクのリスト
        """
        # 現時点では通常の検索と同じ（cross-encoderは将来実装）
        self.logger.info("Reranking is not yet implemented, using standard retrieval")
        return self.retrieve(query, top_k=top_k)
