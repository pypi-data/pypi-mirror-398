"""
RAG Service

RAG (Retrieval-Augmented Generation) コンテキスト取得サービス。
MixinパターンからDIへの移行に対応。
"""

from logging import Logger
from pathlib import Path
from typing import Any

from docgen.utils.logger import get_logger


class RAGService:
    """RAGコンテキスト取得サービス"""

    def __init__(
        self,
        project_root: Path,
        config: dict[str, Any],
        logger: Logger | None = None,
    ):
        """
        初期化

        Args:
            project_root: プロジェクトルートディレクトリ
            config: 設定辞書
            logger: ロガー
        """
        self._project_root = project_root
        self._config = config
        self._logger = logger or get_logger("rag_service")

    @property
    def is_enabled(self) -> bool:
        """RAGが有効かどうか"""
        return self._config.get("rag", {}).get("enabled", False)

    def build_enhanced_query(
        self,
        prompt_name: str,
        project_name: str,
        languages: list[str] | None = None,
        project_info: dict[str, Any] | None = None,
    ) -> str:
        """
        プロジェクト情報を含む詳細なクエリを生成

        Args:
            prompt_name: プロンプト名（例: "project overview", "key_features"）
            project_name: プロジェクト名
            languages: 検出された言語のリスト
            project_info: プロジェクト情報の辞書（オプション）

        Returns:
            改善されたクエリ文字列
        """
        query_parts = []

        # プロジェクト説明を最優先で追加（プロジェクト名の曖昧性を解消）
        # 特に一般的な単語（Locus、Node、Coreなど）の場合は説明を強調
        ambiguous_names = {"locus", "node", "core", "base", "main", "app", "lib", "utils"}
        is_ambiguous = project_name.lower() in ambiguous_names

        # 説明を変数に保存（後で使用するため）
        description = None
        if project_info:
            description = project_info.get("description")

        if description and description.strip():
            # 説明がテンプレートのデフォルトメッセージでない場合のみ追加（多言語対応）
            from docgen.utils.config_utils import get_message

            default_message = get_message(self._config, "default_description")
            if default_message not in description:
                # 説明を強調（曖昧な名前の場合は特に重要）
                desc_text = description[:300]  # より多くの文字を使用
                if is_ambiguous:
                    # 曖昧な名前の場合は説明を最優先で強調
                    query_parts.append(f"IMPORTANT: This project is about: {desc_text.strip()}")
                    query_parts.append(
                        f"Project name '{project_name}' refers to: {desc_text.strip()}"
                    )
                else:
                    query_parts.append(f"Project description: {desc_text.strip()}")
                    query_parts.append(f"Project name: {project_name}")

                # 地理情報関連の誤認を防ぐための明示的な否定（Locusの場合）
                if project_name.lower() == "locus":
                    query_parts.append(
                        "NOT about: geographic location, GPS, mapping, coordinates, geography"
                    )
                    query_parts.append(
                        "IS about: RSS feeds, knowledge management, PKM, personal knowledge"
                    )
            else:
                # 説明がない場合はプロジェクト名のみ
                query_parts.append(f"Project: {project_name}")
        else:
            query_parts.append(f"Project: {project_name}")

        if languages:
            query_parts.append(f"Languages: {', '.join(languages)}")

        if project_info:
            # 主要機能を追加
            if key_features := project_info.get("key_features"):
                if isinstance(key_features, list) and key_features:
                    features_str = ", ".join(key_features[:5])  # 最大5つ
                    query_parts.append(f"Main features: {features_str}")

            # 依存関係から技術スタックを推測
            if dependencies := project_info.get("dependencies"):
                if isinstance(dependencies, dict):
                    tech_list = []
                    for lang, deps in dependencies.items():
                        if deps:
                            tech_list.append(lang)
                    if tech_list:
                        query_parts.append(f"Technologies: {', '.join(tech_list)}")

        # クエリの目的を追加（プロジェクト説明がある場合はより具体的に）
        if project_info and project_info.get("description"):
            query_parts.append(
                f"What are the main components, architecture, and functionality of this project related to {prompt_name}?"
            )
            # 説明を再度強調（特に曖昧な名前の場合）
            if is_ambiguous and description:
                desc_short = description[:150]
                query_parts.append(f"Focus on: {desc_short}")
        else:
            query_parts.append(
                f"What is this project about? What are the main components and functionality related to {prompt_name}?"
            )

        return "\n".join(query_parts)

    def get_context_with_multi_query(
        self,
        base_query: str,
        project_name: str,
        languages: list[str] | None = None,
        project_info: dict[str, Any] | None = None,
        top_k: int | None = None,
    ) -> str:
        """
        マルチクエリ検索を使用してRAGコンテキストを取得

        Args:
            base_query: ベースクエリ
            project_name: プロジェクト名
            languages: 検出された言語のリスト
            project_info: プロジェクト情報の辞書
            top_k: 取得するチャンク数

        Returns:
            フォーマット済みのコンテキスト文字列
        """
        if not self.is_enabled:
            return ""

        try:
            from docgen.rag.retriever import DocumentRetriever

            if top_k is None:
                top_k = self._config.get("rag", {}).get("retrieval", {}).get("top_k", 6)

            retriever = DocumentRetriever(self._config, self._project_root, logger=self._logger)

            # 複数のクエリを生成（プロジェクト説明を活用）
            queries = [
                base_query,
                self.build_enhanced_query(base_query, project_name, languages, project_info),
            ]

            # プロジェクト説明がある場合は、説明ベースのクエリを追加（多言語対応）
            if project_info and project_info.get("description"):
                from docgen.utils.config_utils import get_message

                desc = project_info.get("description", "")
                default_message = get_message(self._config, "default_description")
                if desc and default_message not in desc:
                    # 説明から重要なキーワードを抽出（より多くの文字を使用）
                    desc_snippet = desc[:200]  # より多くの情報を含める
                    queries.append(f"{desc_snippet} architecture and implementation")
                    queries.append(f"{desc_snippet} main components and features")

                    # 地理情報の誤認を防ぐ（Locusの場合）
                    if project_name.lower() == "locus":
                        queries.append("RSS feed knowledge management PKM system")
                        queries.append("RSS aggregation personal knowledge management")
            else:
                # 説明がない場合はプロジェクト名ベースのクエリ
                queries.append(f"{project_name} architecture and main components")
                queries.append(f"{project_name} implementation details and code structure")

            # 各クエリで検索して結果をマージ
            all_chunks = {}
            for query in queries:
                self._logger.debug(f"Searching with query: {query[:50]}...")
                chunks = retriever.retrieve(query, top_k=top_k)
                for chunk in chunks:
                    # ハッシュで重複を除去
                    chunk_hash = chunk.get("hash")
                    if chunk_hash:
                        if chunk_hash not in all_chunks:
                            all_chunks[chunk_hash] = chunk
                        else:
                            # より高いスコアのチャンクを保持
                            existing_score = all_chunks[chunk_hash].get("similarity_score", 0.0)
                            new_score = chunk.get("similarity_score", 0.0)
                            if new_score > existing_score:
                                all_chunks[chunk_hash] = chunk

            chunks_list = list(all_chunks.values())

            if not chunks_list:
                self._logger.warning("No relevant chunks found for multi-query search")
                return ""

            # スコアでソート（降順）
            chunks_list.sort(key=lambda x: x.get("similarity_score", 0.0), reverse=True)

            # top_kに制限
            chunks_list = chunks_list[:top_k]

            formatted_context = retriever.format_context(chunks_list)
            self._logger.info(
                f"Retrieved {len(chunks_list)} relevant chunks from multi-query search"
            )
            return formatted_context

        except Exception as e:
            self._logger.error(f"Multi-query RAG context retrieval error: {e}", exc_info=True)
            # フォールバック: 通常の検索
            return self.get_context(base_query, top_k=top_k)

    def get_context(
        self,
        query: str,
        top_k: int | None = None,
        use_enhanced_query: bool = True,
        project_name: str | None = None,
        languages: list[str] | None = None,
        project_info: dict[str, Any] | None = None,
    ) -> str:
        """
        RAGコンテキストを取得してフォーマット

        Args:
            query: 検索クエリ
            top_k: 取得するチャンク数（Noneの場合は設定ファイルから読み取る）
            use_enhanced_query: 改善されたクエリを使用するかどうか
            project_name: プロジェクト名（改善されたクエリを使用する場合）
            languages: 検出された言語のリスト（改善されたクエリを使用する場合）
            project_info: プロジェクト情報の辞書（改善されたクエリを使用する場合）

        Returns:
            フォーマット済みのコンテキスト文字列（RAG無効時は空文字列）
        """
        if not self.is_enabled:
            return ""

        try:
            from docgen.rag.retriever import DocumentRetriever

            # クエリを改善
            if use_enhanced_query and project_name:
                enhanced_query = self.build_enhanced_query(
                    query, project_name, languages, project_info
                )
                self._logger.info(f"Using enhanced query: {enhanced_query[:100]}...")
                query = enhanced_query
            else:
                self._logger.info(f"Retrieving RAG context for query: {query[:50]}...")

            if top_k is None:
                top_k = self._config.get("rag", {}).get("retrieval", {}).get("top_k", 6)

            retriever = DocumentRetriever(self._config, self._project_root, logger=self._logger)
            chunks = retriever.retrieve(query, top_k=top_k)

            if not chunks:
                self._logger.warning("No relevant chunks found for query")
                return ""

            formatted_context = retriever.format_context(chunks)
            self._logger.info(f"Retrieved {len(chunks)} relevant chunks")
            return formatted_context

        except ImportError:
            self._logger.warning(
                "RAGモジュールが利用できません。"
                "RAG依存関係をインストールしてください: uv sync --extra rag"
            )
            return ""
        except FileNotFoundError as e:
            self._logger.warning(
                f"RAGインデックスが見つかりません: {e}。"
                "インデックスをビルドしてください: uv run python -m docgen.docgen --build-index"
            )
            return ""
        except Exception as e:
            self._logger.error(f"RAGコンテキスト取得中にエラー: {e}", exc_info=True)
            return ""
