"""
LLMクライアントのファクトリークラス
"""

from typing import Any

from ...models.llm import LLMClientConfig
from ...utils.exceptions import ErrorMessages
from ...utils.logger import get_logger
from .anthropic_client import AnthropicClient
from .base import BaseLLMClient
from .local_client import LocalLLMClient
from .openai_client import OpenAIClient

logger = get_logger("llm_clients")


class LLMClientFactory:
    """LLMクライアントのファクトリークラス"""

    @staticmethod
    def create_client(
        config: dict[str, Any] | LLMClientConfig, mode: str = "api"
    ) -> BaseLLMClient | None:
        """
        LLMクライアントを作成

        Args:
            config: LLM設定辞書またはLLMClientConfigオブジェクト
            mode: 'api' または 'local'

        Returns:
            LLMクライアントインスタンス（エラー時はNone）
        """
        try:
            if mode == "api":
                if isinstance(config, LLMClientConfig):
                    client_config = config.openai or config.anthropic
                    if not client_config:
                        logger.error(ErrorMessages.API_CONFIG_NOT_FOUND)
                        return None

                    provider = client_config.provider
                    if provider == "openai":
                        return OpenAIClient(client_config.model_dump())
                    elif provider == "anthropic":
                        return AnthropicClient(client_config.model_dump())
                    else:
                        logger.error(f"サポートされていないAPIプロバイダー: {provider}")
                        return None
                else:
                    api_config = config.get("api", {})
                    provider = api_config.get("provider", "openai")

                    if provider == "openai":
                        return OpenAIClient(api_config)
                    elif provider == "anthropic":
                        return AnthropicClient(api_config)
                    elif provider == "custom":
                        # カスタムエンドポイントはOpenAI互換形式を想定
                        return OpenAIClient(api_config)
                    else:
                        logger.error(f"サポートされていないAPIプロバイダー: {provider}")
                        return None

            elif mode == "local":
                if isinstance(config, dict):
                    local_config = config.get("local", {})
                else:
                    local_config = getattr(config, "local", {})
                    if hasattr(local_config, "model_dump"):
                        local_config = local_config.model_dump()
                return LocalLLMClient(local_config)
            else:
                logger.error(f"サポートされていないモード: {mode}")
                return None

        except ImportError as e:
            logger.warning(f"必要なパッケージがインストールされていません: {e}")
            return None
        except Exception as e:
            logger.error(f"LLMクライアントの作成に失敗しました: {e}")
            return None

    @staticmethod
    def create_client_with_fallback(
        config: dict[str, Any], preferred_mode: str = "api"
    ) -> BaseLLMClient | None:
        """
        LLMクライアントを作成（フォールバック付き）

        Args:
            config: LLM設定辞書
            preferred_mode: 優先するモード（'api' または 'local'）

        Returns:
            LLMクライアントインスタンス（エラー時はNone）
        """
        # 優先モードを試す
        client = LLMClientFactory.create_client(config, preferred_mode)
        if client:
            return client

        # フォールバック: もう一方のモードを試す
        fallback_mode = "local" if preferred_mode == "api" else "api"
        logger.info(f"{preferred_mode}モードが失敗したため、{fallback_mode}モードを試します...")
        return LLMClientFactory.create_client(config, fallback_mode)
