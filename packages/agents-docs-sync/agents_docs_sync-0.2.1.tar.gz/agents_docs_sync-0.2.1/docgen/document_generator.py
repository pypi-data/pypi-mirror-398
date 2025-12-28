"""
ドキュメント生成モジュール
"""

from pathlib import Path
from typing import Any

from .benchmark import BenchmarkContext
from .generator_factory import GeneratorFactory
from .models import DetectedLanguage
from .utils.logger import get_logger

logger = get_logger("document_generator")


class DocumentGenerator:
    """ドキュメント生成クラス"""

    def __init__(
        self,
        project_root: Path,
        detected_languages: list[DetectedLanguage],
        config: dict[str, Any],
        detected_package_managers: dict[str, str] | None = None,
    ):
        """
        初期化

        Args:
            project_root: プロジェクトルートパス
            detected_languages: 検出された言語リスト
            config: 設定辞書
            detected_package_managers: 検出されたパッケージマネージャ辞書
        """
        self.project_root = project_root
        self.detected_languages = detected_languages
        self.config = config
        self.detected_package_managers = detected_package_managers or {}

    def generate_documents(self) -> bool:
        """
        ドキュメントを生成

        Returns:
            成功したかどうか
        """
        if not self.detected_languages:
            logger.warning("サポートされている言語が検出されませんでした")
            return False

        benchmark_enabled = self.config.get("benchmark", {}).get("enabled", False)
        generators_to_run = self._determine_generators_to_run()
        with BenchmarkContext("ドキュメント生成", enabled=benchmark_enabled) as ctx:
            result = self._execute_generators(generators_to_run)
            # 子処理として各ジェネレーターの結果を記録
            if ctx.result and benchmark_enabled:
                # 各ジェネレーターの結果を子処理として追加
                pass  # 子処理の記録は各ジェネレーター内で行う
        return result

    def _determine_generators_to_run(self) -> list[tuple[str, str]]:
        """
        実行するジェネレーターのリストを決定

        Returns:
            (generator_type, display_name)のタプルのリスト
        """
        generators_to_run = []

        # 実行するジェネレーターを決定
        if self.config.get("generation", {}).get("generate_api_doc", True):
            generators_to_run.append(("api", "APIドキュメント"))
            # APIドキュメント生成後にRAGインデックス構築を追加
            rag_config = self.config.get("rag", {})
            if rag_config.get("auto_build_index", False):
                generators_to_run.append(("rag", "RAGインデックス"))

        if self.config.get("generation", {}).get("update_readme", True):
            generators_to_run.append(("readme", "README"))
        if self.config.get("generation", {}).get("generate_agents_doc", True):
            generators_to_run.append(("agents", "AGENTS.md"))
        if self.config.get("generation", {}).get("generate_contributing_doc", False):
            generators_to_run.append(("contributing", "CONTRIBUTING.md"))

        return generators_to_run

    def _execute_generators(self, generators_to_run: list[tuple[str, str]]) -> bool:
        """
        ジェネレーターを実行

        Args:
            generators_to_run: (generator_type, display_name)のタプルのリスト

        Returns:
            すべて成功したかどうか
        """
        success = True

        benchmark_enabled = self.config.get("benchmark", {}).get("enabled", False)

        # 各ジェネレーターを実行
        for gen_type, gen_name in generators_to_run:
            logger.info(f"[{gen_name}生成]")
            if gen_type == "rag":
                # RAGインデックス構築は特殊処理
                with BenchmarkContext(f"{gen_name}生成", enabled=benchmark_enabled):
                    if not self._handle_rag_generation():
                        # ベクトルDB生成の失敗は全体の失敗にはしない
                        logger.warning(
                            "RAGインデックスの構築に失敗しましたが、ドキュメント生成は成功しました"
                        )
                continue

            try:
                with BenchmarkContext(f"{gen_name}生成", enabled=benchmark_enabled):
                    generator = GeneratorFactory.create_generator(
                        gen_type,
                        self.project_root,
                        [lang.name for lang in self.detected_languages],  # 文字列のリストを渡す
                        self.config,
                        self.detected_package_managers,
                    )
                    if generator.generate():
                        logger.info(f"✓ {gen_name}を生成しました")
                    else:
                        logger.error(f"✗ {gen_name}の生成に失敗しました")
                        success = False
            except Exception as e:
                logger.error(f"✗ {gen_name}の生成中にエラーが発生しました: {e}", exc_info=True)
                success = False

        return success

    def _handle_rag_generation(self) -> bool:
        """
        RAGインデックス構築を処理

        Returns:
            成功したかどうか
        """
        try:
            if self._build_vector_index():
                logger.info("✓ RAGインデックスを構築しました")
                return True
            else:
                logger.warning("⚠ RAGインデックスの構築をスキップしました")
                return False
        except Exception as e:
            logger.error(f"✗ RAGインデックスの構築中にエラーが発生しました: {e}", exc_info=True)
            return False

    def _build_vector_index(self) -> bool:
        """
        ベクトルインデックスを構築

        Returns:
            成功したかどうか
        """
        benchmark_enabled = self.config.get("benchmark", {}).get("enabled", False)

        try:
            from .rag.chunker import CodeChunker
            from .rag.embedder import Embedder
            from .rag.indexer import VectorIndexer
        except ImportError as e:
            logger.warning(
                f"RAGモジュールのインポートに失敗しました: {e}\n"
                "RAG依存関係をインストールしてください: uv sync --extra rag"
            )
            return False

        # RAG設定を取得
        rag_config = self.config.get("rag", {})

        # 1. コードベースをチャンク化
        logger.info("Step 1/3: コードベースをチャンク化中...")
        with BenchmarkContext("RAG: チャンク化", enabled=benchmark_enabled):
            # 言語ごとのパターンを収集
            allowed_patterns = []
            for lang in self.detected_languages:
                if lang.rag_enabled:
                    allowed_patterns.extend(lang.get_rag_patterns())

            if allowed_patterns:
                logger.info(f"RAG対象パターン: {allowed_patterns}")

            chunker = CodeChunker(rag_config)
            chunks = chunker.chunk_codebase(
                self.project_root, allowed_patterns=allowed_patterns if allowed_patterns else None
            )

        if not chunks:
            logger.warning("チャンクが見つかりませんでした")
            return False

        logger.info(f"✓ {len(chunks)} 個のチャンクを作成しました")

        # 2. 埋め込み生成
        logger.info("Step 2/3: 埋め込みを生成中...")
        with BenchmarkContext("RAG: 埋め込み生成", enabled=benchmark_enabled):
            embedder = Embedder(rag_config)

            # チャンクのテキストを抽出
            texts = [chunk["text"] for chunk in chunks]

            # バッチ処理で埋め込み生成
            embeddings = embedder.embed_batch(texts, batch_size=32)

        logger.info(f"✓ {len(embeddings)} 個の埋め込みを生成しました")

        # 3. インデックス構築
        logger.info("Step 3/3: インデックスを構築中...")
        with BenchmarkContext("RAG: インデックス構築", enabled=benchmark_enabled):
            index_dir = self.project_root / "docgen" / "index"
            indexer = VectorIndexer(
                index_dir=index_dir,
                embedding_dim=embedder.embedding_dim,
                config=rag_config,
            )

            # インデックス構築
            indexer.build(embeddings, chunks)

            # 保存
            indexer.save()

        logger.info(f"✓ インデックスを保存しました: {index_dir}")
        logger.info("=" * 60)
        logger.info(f"インデックスディレクトリ: {index_dir}")
        logger.info(f"チャンク数: {len(chunks)}")
        logger.info(f"埋め込み次元: {embedder.embedding_dim}")

        return True
