"""
Service Container

サービス依存関係を管理するコンテナクラス。
DI（Dependency Injection）パターンの実装。
"""

from dataclasses import dataclass

from .formatting_service import FormattingService
from .llm_service import LLMService
from .manual_section_service import ManualSectionService
from .rag_service import RAGService
from .template_service import TemplateService


@dataclass
class ServiceContainer:
    """サービスコンテナ

    全てのジェネレーター用サービスを一箇所に集約し、
    依存関係を明示的に管理します。

    Attributes:
        llm_service: LLM連携サービス
        template_service: テンプレートレンダリングサービス
        formatting_service: テキスト整形サービス
        manual_section_service: 手動セクション管理サービス
        rag_service: RAGコンテキスト取得サービス（オプショナル）
    """

    llm_service: LLMService
    template_service: TemplateService
    formatting_service: FormattingService
    manual_section_service: ManualSectionService
    rag_service: RAGService | None = None

    def __post_init__(self):
        """初期化後の検証"""
        # 必須サービスが全て設定されているか確認
        required_services = [
            ("llm_service", self.llm_service),
            ("template_service", self.template_service),
            ("formatting_service", self.formatting_service),
            ("manual_section_service", self.manual_section_service),
        ]

        for service_name, service in required_services:
            if service is None:
                raise ValueError(f"{service_name} must not be None")
