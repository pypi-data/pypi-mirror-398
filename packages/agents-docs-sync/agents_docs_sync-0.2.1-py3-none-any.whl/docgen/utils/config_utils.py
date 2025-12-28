"""
設定アクセスユーティリティ
"""

from typing import Any


def get_nested_config(config: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """
    ネストされた設定値を安全に取得

    Args:
        config: 設定辞書
        *keys: 取得するキーのパス
        default: デフォルト値

    Returns:
        設定値。存在しない場合はdefault

    Examples:
        >>> config = {"a": {"b": {"c": "value"}}}
        >>> get_nested_config(config, "a", "b", "c")
        'value'
        >>> get_nested_config(config, "a", "x", "y", default="default")
        'default'
    """
    current = config
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def get_config_bool(config: dict[str, Any], *keys: str, default: bool = False) -> bool:
    """
    設定値をブール値として取得

    Args:
        config: 設定辞書
        *keys: 取得するキーのパス
        default: デフォルト値

    Returns:
        ブール値
    """
    value = get_nested_config(config, *keys, default=default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


def get_config_list(config: dict[str, Any], *keys: str, default: list | None = None) -> list:
    """
    設定値をリストとして取得

    Args:
        config: 設定辞書
        *keys: 取得するキーのパス
        default: デフォルト値

    Returns:
        リスト
    """
    if default is None:
        default = []
    value = get_nested_config(config, *keys, default=default)
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        # カンマ区切りをサポート
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, (int, float)):
        return [value]
    return default


def get_config_str(config: dict[str, Any], *keys: str, default: str = "") -> str:
    """
    設定値を文字列として取得

    Args:
        config: 設定辞書
        *keys: 取得するキーのパス
        default: デフォルト値

    Returns:
        文字列
    """
    value = get_nested_config(config, *keys, default=default)
    if value is None:
        return default
    if isinstance(value, str):
        return value
    return str(value)


def get_message(
    config: dict[str, Any] | None, message_key: str, language: str | None = None
) -> str:
    """
    メッセージを取得

    Args:
        config: 設定辞書（Noneの場合はデフォルト値を使用）
        message_key: メッセージキー（例: "default_description"）
        language: 言語コード（互換性のため残しているが、現在は使用されない）

    Returns:
        メッセージ文字列
    """
    # デフォルトメッセージ
    default_messages: dict[str, str] = {
        "default_description": "Please describe this project here.",
    }

    # 設定からメッセージを取得
    if config:
        messages = config.get("messages", {})
        message_value = messages.get(message_key)
        if message_value is not None:
            # 文字列の場合はそのまま返す（新しい形式）
            if isinstance(message_value, str):
                return message_value
            # 辞書の場合は従来通り言語に応じて取得（後方互換性）
            if isinstance(message_value, dict):
                if language is None:
                    language = config.get("general", {}).get("default_language", "en")
                if language in message_value:
                    return message_value[language]
                # フォールバック: 英語または最初の値
                return message_value.get("en", next(iter(message_value.values()), ""))

    # デフォルトメッセージから取得
    if message_key in default_messages:
        return default_messages[message_key]

    # フォールバック
    return ""
