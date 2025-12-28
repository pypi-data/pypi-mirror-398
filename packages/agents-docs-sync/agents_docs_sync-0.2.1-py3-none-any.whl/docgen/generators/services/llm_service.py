"""
LLM Service

LLMを使用したコンテンツ生成サービス。
MixinパターンからDIへの移行に対応。
"""

from logging import Logger
from typing import Any

from docgen.utils.llm import LLMClientFactory
from docgen.utils.logger import get_logger


class LLMService:
    """LLM生成サービス"""

    def __init__(
        self,
        config: dict[str, Any],
        logger: Logger | None = None,
    ):
        """
        初期化

        Args:
            config: 設定辞書（agents設定を含む）
            logger: ロガー
        """
        self._config = config
        self._logger = logger or get_logger("llm_service")
        self._client: Any = None

    @property
    def agents_config(self) -> dict[str, Any]:
        """agents設定を取得"""
        return self._config.get("agents", {})

    def get_client(self) -> Any:
        """
        LLMクライアントを取得（フォールバック付き）

        Returns:
            LLMクライアント（取得できない場合はNone）
        """
        if self._client is not None:
            return self._client

        llm_mode = self.agents_config.get("llm_mode", "api")
        preferred_mode = "api" if llm_mode == "api" else "local"

        self._client = LLMClientFactory.create_client_with_fallback(
            self.agents_config, preferred_mode=preferred_mode
        )
        return self._client

    def generate(self, prompt: str) -> str:
        """
        LLMを使用してテキストを生成

        Args:
            prompt: 入力プロンプト

        Returns:
            生成されたテキスト

        Raises:
            RuntimeError: LLMクライアントが利用できない場合
        """
        client = self.get_client()
        if not client:
            raise RuntimeError("LLMクライアントが利用できません")

        return client.generate(prompt)

    def should_use_outlines(self) -> bool:
        """
        Outlinesを使用するかどうかを判定

        Returns:
            Outlinesを使用するかどうか
        """
        from docgen.utils.outlines_utils import should_use_outlines

        return should_use_outlines(self.agents_config)

    def create_outlines_model(self, client: Any) -> Any:
        """
        Outlinesモデルを作成

        Args:
            client: LLMクライアント

        Returns:
            Outlinesモデル（サポートされない場合はNone）
        """
        from docgen.utils.outlines_utils import create_outlines_model

        return create_outlines_model(client)

    def format_project_info(
        self,
        project_info: Any,
        languages: list[str],
        package_managers: dict[str, str] | None = None,
    ) -> str:
        """
        プロジェクト情報をプロンプト用に整形

        Args:
            project_info: プロジェクト情報
            languages: 言語リスト
            package_managers: パッケージマネージャ辞書

        Returns:
            整形された文字列
        """
        info_parts = []
        # project_root.name は project_info に含まれていないため、呼び出し元で処理するか、
        # ここでは project_info の中身だけを整形する。
        # Mixinの実装を見ると self.project_root.name を使っている。
        # 引数として project_name を受け取るように変更するか、project_info に name を持たせるのが良いが、
        # ここではシンプルに project_info の内容を整形する。

        info_parts.append(f"Description: {project_info.description}")
        info_parts.append(f"Languages: {', '.join(languages)}")

        if package_managers:
            pms = [f"{lang}: {pm}" for lang, pm in package_managers.items()]
            info_parts.append(f"Package Managers: {', '.join(pms)}")

        if project_info.dependencies:
            deps = []
            # ignored言語の依存関係は含めない
            if "python" in project_info.dependencies and "python" in languages:
                deps.extend(project_info.dependencies["python"])
            if "nodejs" in project_info.dependencies and (
                "javascript" in languages or "typescript" in languages
            ):
                deps.extend(project_info.dependencies["nodejs"])
            if deps:
                info_parts.append(f"Dependencies: {', '.join(deps[:20])}...")

        return "\n".join(info_parts)

    def generate_content(
        self,
        prompt_file: str,
        prompt_name: str,
        project_info_str: str,
        rag_context: str = "",
    ) -> str:
        """
        LLMを使用して特定のコンテンツを生成

        Args:
            prompt_file: プロンプトファイル名
            prompt_name: プロンプト名
            project_info_str: 整形済みプロジェクト情報
            rag_context: RAGコンテキスト

        Returns:
            生成されたコンテンツ
        """
        try:
            client = self.get_client()
            if not client:
                self._logger.warning(
                    f"LLMクライアントが利用できません。{prompt_name}の生成をスキップします。"
                )
                return ""

            self._logger.info(f"LLMを使用して{prompt_name}を生成中...")

            from docgen.utils.prompt_loader import PromptLoader

            if rag_context:
                prompt = PromptLoader.load_prompt(
                    prompt_file,
                    f"{prompt_name}_with_rag",
                    config=self._config,
                    project_info=project_info_str,
                    rag_context=rag_context,
                )
            else:
                prompt = PromptLoader.load_prompt(
                    prompt_file,
                    prompt_name,
                    config=self._config,
                    project_info=project_info_str,
                )

            response = client.generate(prompt)

            # クリーニングは呼び出し元で行うか、ここで行うか。
            # FormattingServiceに依存したくないので、最低限のクリーニングを行うか、
            # 生のレスポンスを返す。ここでは生のレスポンスを返す。
            return response

        except Exception as e:
            self._logger.warning(f"{prompt_name}の生成中にエラーが発生しました: {e}")
            return ""
