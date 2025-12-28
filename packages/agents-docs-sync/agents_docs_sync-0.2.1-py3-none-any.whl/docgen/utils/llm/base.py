"""
LLMクライアントの基底クラスと共通ユーティリティ
"""

from abc import ABC, abstractmethod
import os
import time
from typing import Any

from ...models.llm import LLMConfig
from ...utils.exceptions import ConfigError, ErrorMessages
from ...utils.logger import get_logger

logger = get_logger("llm_clients")

# Default LLM models
DEFAULT_MODELS = {
    "openai": "gpt-4o",
    "anthropic": "claude-3-5-sonnet-20241022",
    "ollama": "llama3",
    "lmstudio": "llama3",
}


class LLMClientInitializer:
    """Common initialization patterns for LLM clients."""

    @staticmethod
    def setup_provider_config(config: dict[str, Any], provider: str) -> dict[str, Any]:
        """
        Set up provider-specific configuration.

        Args:
            config: Configuration dictionary
            provider: Provider name ('openai', 'anthropic', etc.)

        Returns:
            Updated configuration dictionary
        """
        if isinstance(config, dict):
            config = config.copy()
            config["provider"] = provider
        return config

    @staticmethod
    def get_api_key(config, env_var: str, default_env: str) -> str:
        """
        Get API key from config or environment.

        Args:
            config: LLMConfig object
            env_var: Environment variable name from config
            default_env: Default environment variable name

        Returns:
            API key string
        """
        env_name = getattr(config, "api_key_env", None) or default_env
        api_key = getattr(config, "api_key", None) or os.getenv(env_name, "")
        return api_key or ""

    @staticmethod
    def initialize_client_with_fallback(
        client_class, config: dict[str, Any], import_name: str, package_name: str, error_prefix: str
    ):
        """
        Initialize LLM client with common error handling.

        Args:
            client_class: Client class to instantiate
            config: Configuration dictionary
            import_name: Module name to import
            package_name: Package name for error messages
            error_prefix: Prefix for error messages

        Returns:
            Initialized client instance

        Raises:
            ImportError: If required package is not installed
            ConfigError: If initialization fails
        """
        try:
            # Import the module
            __import__(import_name)

            # Create client instance
            return client_class(config)

        except ImportError:
            raise ImportError(
                f"{package_name}パッケージが必要です。`pip install {package_name}`でインストールしてください。"
            ) from None
        except Exception as e:
            raise ConfigError(
                ErrorMessages.CLIENT_INIT_FAILED.format(prefix=error_prefix, error=e)
            ) from e


class BaseLLMClient(ABC):
    """LLMクライアントの抽象基底クラス"""

    def __init__(self, config: dict[str, Any] | LLMConfig):
        """
        初期化

        Args:
            config: LLM設定辞書またはLLMConfigオブジェクト
        """
        if isinstance(config, dict):
            self.config = LLMConfig(**config)
        else:
            self.config = config

        self.timeout: int = self.config.timeout
        self.max_retries: int = self.config.max_retries
        self.retry_delay: float = self.config.retry_delay

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str | None = None, **kwargs) -> str | None:
        """
        テキストを生成

        Args:
            prompt: プロンプト
            system_prompt: システムプロンプト（オプション）
            **kwargs: その他のパラメータ

        Returns:
            生成されたテキスト（エラー時はNone）
        """
        pass

    def create_outlines_model(self):
        """
        Outlinesモデルを作成

        Returns:
            Outlinesモデルインスタンス（Outlinesが利用できない場合はNone）
        """
        try:
            import outlines

            return self._create_outlines_model_internal(outlines)
        except ImportError:
            logger.warning("Outlinesがインストールされていません")
            return None
        except Exception as e:
            logger.error(f"Outlinesモデルの作成に失敗しました: {e}")
            return None

    @abstractmethod
    def _create_outlines_model_internal(self, outlines):
        """
        Outlinesモデルを作成（内部実装）

        Args:
            outlines: Outlinesモジュール

        Returns:
            Outlinesモデルインスタンス
        """
        pass

    def _retry_with_backoff(self, func, *args, **kwargs):
        """
        リトライ機能付きで関数を実行

        Args:
            func: 実行する関数
            *args: 関数の引数
            **kwargs: 関数のキーワード引数

        Returns:
            関数の戻り値
        """
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    logger.warning(
                        f"LLM呼び出し失敗 (試行 {attempt + 1}/{self.max_retries}): {e}. {delay}秒後にリトライします..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"LLM呼び出しが{self.max_retries}回失敗しました: {e}")
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError(ErrorMessages.LLM_UNKNOWN_ERROR)
