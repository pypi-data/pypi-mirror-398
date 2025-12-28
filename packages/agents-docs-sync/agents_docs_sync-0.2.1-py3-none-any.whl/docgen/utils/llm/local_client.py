"""
ローカルLLMクライアント（Ollama、LM Studio対応）
"""

from typing import Any

from ...utils.exceptions import ConfigError, ErrorMessages, LLMError
from ...utils.logger import get_logger
from .base import BaseLLMClient

logger = get_logger("llm_clients")


class LocalLLMClient(BaseLLMClient):
    """ローカルLLMクライアント（Ollama、LM Studio対応）"""

    def __init__(self, config: dict[str, Any]):
        # LocalLLMクライアント用にproviderを設定（既に設定されている場合は上書きしない）
        if isinstance(config, dict) and "provider" not in config:
            config["provider"] = "local"
        super().__init__(config)
        try:
            import httpx

            # httpxクライアントを作成（接続プールを使用）
            self.httpx_client = httpx.Client(timeout=self.timeout)
            self.httpx = httpx
        except ImportError:
            raise ImportError(
                "httpxパッケージが必要です。`pip install httpx`でインストールしてください。"
            ) from None

        self.base_url: str = self.config.base_url or "http://localhost:11434"
        self.model: str = config.get("model", "llama3")
        self.provider: str = config.get("provider", "ollama")
        logger.info(
            f"LLM Client initialized: provider={self.provider}, base_url={self.base_url}, model={self.model}"
        )

        # ベースURLの正規化（末尾のスラッシュを削除）
        self.base_url = self.base_url.rstrip("/")

    def generate(self, prompt: str, system_prompt: str | None = None, **kwargs) -> str | None:
        """ローカルLLMを使用してテキストを生成"""
        try:
            # LocalLLMClientは常にローカルプロバイダーとして動作
            if self.config.provider == "ollama":
                return self._generate_ollama(prompt, system_prompt, **kwargs)
            elif self.config.provider in ["lmstudio", "custom", "local"]:
                return self._generate_openai_compatible(prompt, system_prompt, **kwargs)
            else:
                raise ConfigError(
                    ErrorMessages.UNSUPPORTED_PROVIDER.format(provider=self.config.provider)
                )
        except (ConfigError, LLMError):
            raise
        except Exception as e:
            logger.error(f"ローカルLLM呼び出しエラー: {e}", exc_info=True)
            return None

    def _create_outlines_model_internal(self, outlines):
        """ローカルLLM用のOutlinesモデルを作成"""
        # OpenAI互換APIとして扱う
        import openai

        openai_client = openai.OpenAI(
            base_url=self.base_url,
            api_key="dummy",  # ローカルでは不要
        )
        return outlines.from_openai(openai_client, self.model)

    def _generate_ollama(
        self, prompt: str, system_prompt: str | None = None, **kwargs
    ) -> str | None:
        """Ollama APIを使用してテキストを生成"""
        try:
            # OllamaのAPI形式
            url = f"{self.base_url}/api/generate"

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            }

            if system_prompt:
                payload["system"] = system_prompt

            response = self._retry_with_backoff(
                lambda: self.httpx.post(url, json=payload, timeout=self.timeout)
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("response", "").strip()
            else:
                logger.error(f"Ollama APIエラー: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Ollama API呼び出しエラー: {e}")
            return None

    def _generate_openai_compatible(
        self, prompt: str, system_prompt: str | None = None, **kwargs
    ) -> str | None:
        """OpenAI互換APIを使用してテキストを生成（LM Studio等）"""
        try:
            # OpenAI互換のAPI形式
            url = f"{self.base_url}/v1/chat/completions"
            logger.info(f"Connecting to LLM API: {url}")

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 4096),
            }

            response = self._retry_with_backoff(lambda: self.httpx_client.post(url, json=payload))

            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"].strip()
                return None
            else:
                logger.error(f"OpenAI互換APIエラー: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"OpenAI互換API呼び出しエラー: {e}")
            return None
