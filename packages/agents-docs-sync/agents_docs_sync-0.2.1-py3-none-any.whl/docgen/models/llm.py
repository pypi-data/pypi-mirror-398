"""LLM related Pydantic models."""

from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM設定モデル"""

    provider: str | None = Field(
        default=None, description="LLMプロバイダー (openai, anthropic, ollama, local)"
    )
    model: str | None = Field(default=None, description="モデル名")
    api_key: str | None = Field(default=None, description="APIキー")
    api_key_env: str | None = Field(default=None, description="APIキー環境変数名")
    base_url: str | None = Field(default=None, description="ベースURL")
    endpoint: str | None = Field(default=None, description="エンドポイントURL")
    timeout: int = Field(default=30, description="タイムアウト秒数")
    max_retries: int = Field(default=3, description="最大リトライ回数")
    retry_delay: float = Field(default=1.0, description="リトライ遅延秒数")
    temperature: float | None = Field(default=None, description="温度パラメータ")
    max_tokens: int | None = Field(default=None, description="最大トークン数")


class LLMClientConfig(BaseModel):
    """LLMクライアント設定モデル"""

    openai: LLMConfig | None = Field(default=None, description="OpenAI設定")
    anthropic: LLMConfig | None = Field(default=None, description="Anthropic設定")
    ollama: LLMConfig | None = Field(default=None, description="Ollama設定")
    local: LLMConfig | None = Field(default=None, description="ローカルLLM設定")
    default_provider: str = Field(default="openai", description="デフォルトプロバイダー")
