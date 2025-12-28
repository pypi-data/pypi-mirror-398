"""
Anthropic APIクライアント
"""

from typing import Any

from ...utils.exceptions import LLMError
from ...utils.logger import get_logger
from .base import DEFAULT_MODELS, BaseLLMClient, LLMClientInitializer

logger = get_logger("llm_clients")


class AnthropicClient(BaseLLMClient):
    """Anthropic APIクライアント"""

    def __init__(self, config: dict[str, Any]):
        # Anthropicクライアント用にproviderを設定
        config = LLMClientInitializer.setup_provider_config(config, "anthropic")
        super().__init__(config)

        # Anthropicクライアントの初期化
        def create_anthropic_client(config):
            import anthropic

            # configが辞書の場合はgetattrで取得、オブジェクトの場合は属性アクセス
            api_key_env = config.get("api_key_env") if isinstance(config, dict) else getattr(config, "api_key_env", None)
            api_key = LLMClientInitializer.get_api_key(
                config, api_key_env, "ANTHROPIC_API_KEY"
            )
            return anthropic.Anthropic(api_key=api_key)

        config_dict = self.config.model_dump() if hasattr(self.config, "model_dump") else self.config
        self.client = LLMClientInitializer.initialize_client_with_fallback(
            create_anthropic_client, config_dict, "anthropic", "anthropic", "Anthropic"  # type: ignore[arg-type]
        )
        self.model = self.config.model or DEFAULT_MODELS["anthropic"]

    def generate(self, prompt: str, system_prompt: str | None = None, **kwargs) -> str | None:
        """Anthropic APIを使用してテキストを生成"""
        try:
            messages = [{"role": "user", "content": prompt}]

            api_kwargs = {
                "model": self.model,
                "max_tokens": kwargs.get("max_tokens", 4096),
                "messages": messages,
                "timeout": self.timeout,
            }

            if system_prompt:
                api_kwargs["system"] = system_prompt

            response = self._retry_with_backoff(self.client.messages.create, **api_kwargs)

            if response and response.content:
                # Anthropicのレスポンス形式に合わせて処理
                text_content = ""
                for block in response.content:
                    if hasattr(block, "text") and block.text:
                        text_content += block.text
                return text_content.strip() if text_content else None
            return None
        except LLMError:
            raise
        except Exception as e:
            logger.error(f"Anthropic API呼び出しエラー: {e}", exc_info=True)
            return None

    def _create_outlines_model_internal(self, outlines):
        """Anthropic用のOutlinesモデルを作成（現在未対応）"""
        # Outlinesは現在Anthropicを直接サポートしていないため、未実装
        logger.warning("Anthropic用のOutlinesモデルは現在サポートされていません")
        return None
