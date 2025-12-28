"""
カスタム例外クラス
ドキュメント生成システムで使用する例外を定義
"""

from typing import Any


class ErrorMessages:
    """共通エラーメッセージ定数"""

    CONFIG_LOAD_FAILED = "設定ファイルの読み込みに失敗しました"
    CONFIG_NOT_FOUND = "設定ファイルが見つかりません: {path}"
    CACHE_LOAD_FAILED = "キャッシュファイルの読み込みに失敗しました: {error}"
    API_CONFIG_NOT_FOUND = "API設定が見つかりません"
    GIT_COMMAND_NOT_FOUND = "gitコマンドが見つかりません。"
    HOOKS_DIR_NOT_FOUND = "docgen/hooks ディレクトリが見つかりません"
    HOOK_SOURCE_NOT_FOUND = "{hook_name} のソースファイルが見つかりません: {source_file}"
    LLM_UNKNOWN_ERROR = "LLM呼び出しで不明なエラーが発生しました"
    CLIENT_INIT_FAILED = "{prefix}クライアントの初期化に失敗しました: {error}"
    UNSUPPORTED_PROVIDER = "サポートされていないプロバイダー: {provider}"


class DocGenError(Exception):
    """ドキュメント生成システムの基本例外クラス"""

    def __init__(
        self,
        message: str,
        details: str | None = None,
        error_code: str | None = None,
        context: dict[str, Any] | None = None,
    ):
        self.message = message
        self.details = details
        self.error_code = error_code
        self.context = context

    def __str__(self) -> str:
        result = self.message
        if self.details:
            result += f": {self.details}"
        # エラーコードはデバッグ時のみ表示
        # if self.error_code:
        #     result += f" (code: {self.error_code})"
        return result


class ConfigError(DocGenError):
    """設定関連のエラー"""

    def __init__(self, message: str, config_path: str | None = None, **kwargs):
        # 第2引数をdetailsとして扱う（後方互換性のため）
        details = kwargs.get("details") or config_path
        super().__init__(
            message=message,
            details=details,
            error_code="CONFIG_ERROR",
            context={"config_path": config_path} if config_path else None,
            **kwargs,
        )


class LLMError(DocGenError):
    """LLM関連のエラー"""

    def __init__(
        self, message: str, provider: str | None = None, model: str | None = None, **kwargs
    ):
        # 第2引数をdetailsとして扱う（後方互換性のため）
        details = kwargs.get("details") or provider
        super().__init__(
            message=message,
            details=details,
            error_code="LLM_ERROR",
            context={"provider": provider, "model": model} if provider or model else None,
            **kwargs,
        )


class ParseError(DocGenError):
    """解析関連のエラー"""

    def __init__(
        self, message: str, file_path: str | None = None, language: str | None = None, **kwargs
    ):
        # 第2引数をdetailsとして扱う（後方互換性のため）
        details = kwargs.get("details") or file_path
        super().__init__(
            message=message,
            details=details,
            error_code="PARSE_ERROR",
            context={"file_path": file_path, "language": language}
            if file_path or language
            else None,
            **kwargs,
        )


class CacheError(DocGenError):
    """キャッシュ関連のエラー"""

    def __init__(self, message: str, cache_key: str | None = None, **kwargs):
        # 第2引数をdetailsとして扱う（後方互換性のため）
        details = kwargs.get("details") or cache_key
        super().__init__(
            message=message,
            details=details,
            error_code="CACHE_ERROR",
            context={"cache_key": cache_key} if cache_key else None,
            **kwargs,
        )


class FileOperationError(DocGenError):
    """ファイル操作関連のエラー"""

    def __init__(
        self, message: str, file_path: str | None = None, operation: str | None = None, **kwargs
    ):
        # 第2引数をdetailsとして扱う（後方互換性のため）
        details = kwargs.get("details") or file_path
        super().__init__(
            message=message,
            details=details,
            error_code="FILE_ERROR",
            context={"file_path": file_path, "operation": operation}
            if file_path or operation
            else None,
            **kwargs,
        )


class GenerationError(DocGenError):
    """ドキュメント生成関連のエラー"""

    def __init__(
        self,
        message: str,
        doc_type: str | None = None,
        generator: str | None = None,
        **kwargs,
    ):
        # 第2引数をdetailsとして扱う（後方互換性のため）
        details = kwargs.get("details") or doc_type
        super().__init__(
            message=message,
            details=details,
            error_code="GENERATION_ERROR",
            context={"doc_type": doc_type, "generator": generator}
            if doc_type or generator
            else None,
            **kwargs,
        )


class HookError(DocGenError):
    """フック関連のエラー"""

    def __init__(self, message: str, hook_name: str | None = None, **kwargs):
        details = kwargs.get("details") or hook_name
        super().__init__(
            message=message,
            details=details,
            error_code="HOOK_ERROR",
            context={"hook_name": hook_name} if hook_name else None,
            **kwargs,
        )


class TemplateError(DocGenError):
    """テンプレート関連のエラー"""

    def __init__(self, message: str, template_name: str | None = None, **kwargs):
        details = kwargs.get("details") or template_name
        super().__init__(
            message=message,
            details=details,
            error_code="TEMPLATE_ERROR",
            context={"template_name": template_name} if template_name else None,
            **kwargs,
        )
