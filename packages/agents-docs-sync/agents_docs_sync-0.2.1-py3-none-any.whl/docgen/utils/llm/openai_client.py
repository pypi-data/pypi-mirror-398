"""
OpenAI APIクライアント
"""

from typing import Any

from ...utils.exceptions import LLMError
from ...utils.logger import get_logger
from .base import DEFAULT_MODELS, BaseLLMClient, LLMClientInitializer

logger = get_logger("llm_clients")


class OpenAIClient(BaseLLMClient):
    """OpenAI APIクライアント"""

    def __init__(self, config: dict[str, Any]):
        # OpenAIクライアント用にproviderを設定
        config = LLMClientInitializer.setup_provider_config(config, "openai")
        super().__init__(config)

        # OpenAIクライアントの初期化
        def create_openai_client(config):
            import openai

            # configが辞書の場合はgetattrで取得、オブジェクトの場合は属性アクセス
            api_key_env = config.get("api_key_env") if isinstance(config, dict) else getattr(config, "api_key_env", None)
            api_key = LLMClientInitializer.get_api_key(config, api_key_env, "OPENAI_API_KEY")
            base_url = config.get("base_url") if isinstance(config, dict) else getattr(config, "base_url", None)
            return openai.OpenAI(
                api_key=api_key,
                base_url=base_url,  # カスタムエンドポイント対応
            )

        config_dict = self.config.model_dump() if hasattr(self.config, "model_dump") else self.config
        self.client = LLMClientInitializer.initialize_client_with_fallback(
            create_openai_client, config_dict, "openai", "openai", "OpenAI"  # type: ignore[arg-type]
        )
        self.model: str = self.config.model or DEFAULT_MODELS["openai"]

    def generate(self, prompt: str, system_prompt: str | None = None, **kwargs) -> str | None:
        """OpenAI APIを使用してテキストを生成"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            api_kwargs = {
                "model": self.model,
                "max_tokens": kwargs.get("max_tokens", 4096),
                "messages": messages,
                "timeout": self.timeout,
            }

            response = self._retry_with_backoff(self.client.chat.completions.create, **api_kwargs)

            if response and response.choices:
                return response.choices[0].message.content
            return None
        except LLMError:
            raise
        except Exception as e:
            logger.error(f"OpenAI API呼び出しエラー: {e}", exc_info=True)
            return None

    def _create_outlines_model_internal(self, outlines):
        """OpenAI用のOutlinesモデルを作成"""
        return outlines.from_openai(self.client, self.model)
