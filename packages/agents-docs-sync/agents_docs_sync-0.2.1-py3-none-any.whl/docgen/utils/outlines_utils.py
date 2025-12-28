"""
Outlines統合ユーティリティモジュール
共通のOutlines関連機能をまとめる
"""

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from types import ModuleType

try:
    import outlines

    OUTLINES_AVAILABLE = True
except ImportError:
    OUTLINES_AVAILABLE = False
    outlines = None  # type: ignore[assignment, no-redef]


def should_use_outlines(config: dict[str, Any]) -> bool:
    """
    Outlinesを使用するかどうかを判定

    Args:
        config: 設定辞書

    Returns:
        Outlinesを使用するかどうか
    """
    # Outlinesライブラリが利用可能かチェック
    if not OUTLINES_AVAILABLE:
        return False

    # 設定でOutlinesが有効になっているかチェック
    return config.get("use_outlines", False)


def create_outlines_model(client, provider: str = "openai"):
    """
    Outlinesモデルを作成

    Args:
        client: LLMクライアント
        provider: プロバイダー名 ('openai', 'anthropic', 'local')

    Returns:
        Outlinesモデルインスタンス（作成できない場合はNone）
    """
    if not OUTLINES_AVAILABLE:
        return None

    try:
        # クライアントの種類に応じてOutlinesモデルを作成
        if hasattr(client, "client") and hasattr(client.client, "api_key"):
            # OpenAIクライアント
            if outlines is not None:
                return outlines.from_openai(client.client, client.model)  # type: ignore
        elif hasattr(client, "base_url"):
            # ローカルLLMクライアント
            provider = getattr(client, "provider", "ollama")

            if provider == "ollama":
                # Ollamaの場合
                if outlines is not None:
                    return outlines.from_ollama(client.model, client.base_url)  # type: ignore
            else:
                # その他のローカルLLMはOpenAI互換APIとして扱う
                import openai

                openai_client = openai.OpenAI(
                    base_url=f"{client.base_url}"
                    if client.base_url.rstrip("/").endswith("/v1")
                    else f"{client.base_url}/v1",
                    api_key="dummy",  # ローカルでは不要
                )
                if outlines is not None:
                    return outlines.from_openai(openai_client, client.model)  # type: ignore
        else:
            raise ValueError("サポートされていないクライアントタイプ")
    except Exception:
        # エラーログは呼び出し元で処理
        return None
