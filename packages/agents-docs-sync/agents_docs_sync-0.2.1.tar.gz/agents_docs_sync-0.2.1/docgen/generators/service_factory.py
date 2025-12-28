"""
Service Factory

ジェネレーター用のサービスを一元的に生成するファクトリクラス。
"""

from logging import Logger
from pathlib import Path
from typing import Any

from docgen.generators.services.formatting_service import FormattingService
from docgen.generators.services.llm_service import LLMService
from docgen.generators.services.manual_section_service import ManualSectionService
from docgen.generators.services.rag_service import RAGService
from docgen.generators.services.service_container import ServiceContainer
from docgen.generators.services.template_service import TemplateService
from docgen.utils.logger import get_logger


class GeneratorServiceFactory:
    """ジェネレーターサービスファクトリ"""

    @staticmethod
    def create_container(
        project_root: Path,
        config: dict[str, Any],
        logger: Logger | None = None,
    ) -> ServiceContainer:
        """
        ServiceContainerを生成して返す

        Args:
            project_root: プロジェクトルートディレクトリ
            config: 設定辞書
            logger: ロガー（各サービスに渡される）

        Returns:
            ServiceContainerインスタンス
        """
        logger = logger or get_logger("service_factory")

        return ServiceContainer(
            llm_service=LLMService(config=config, logger=logger),
            template_service=TemplateService(),
            rag_service=RAGService(project_root=project_root, config=config, logger=logger),
            formatting_service=FormattingService(),
            manual_section_service=ManualSectionService(),
        )

    @staticmethod
    def create_services(
        project_root: Path,
        config: dict[str, Any],
        logger: Logger | None = None,
    ) -> dict[str, Any]:
        """
        全サービスを生成して返す（後方互換性のため）

        Args:
            project_root: プロジェクトルートディレクトリ
            config: 設定辞書
            logger: ロガー（各サービスに渡される）

        Returns:
            サービスインスタンスの辞書
        """
        container = GeneratorServiceFactory.create_container(project_root, config, logger)

        return {
            "llm": container.llm_service,
            "template": container.template_service,
            "rag": container.rag_service,
            "formatting": container.formatting_service,
            "manual_section": container.manual_section_service,
        }

    @staticmethod
    def create_llm_service(config: dict[str, Any], logger: Logger | None = None) -> LLMService:
        """LLMServiceを個別に生成"""
        return LLMService(config=config, logger=logger)

    @staticmethod
    def create_template_service(template_dir: Path | None = None) -> TemplateService:
        """TemplateServiceを個別に生成"""
        return TemplateService(template_dir=template_dir)

    @staticmethod
    def create_rag_service(
        project_root: Path, config: dict[str, Any], logger: Logger | None = None
    ) -> RAGService:
        """RAGServiceを個別に生成"""
        return RAGService(project_root=project_root, config=config, logger=logger)

    @staticmethod
    def create_formatting_service() -> FormattingService:
        """FormattingServiceを個別に生成"""
        return FormattingService()

    @staticmethod
    def create_manual_section_service() -> ManualSectionService:
        """ManualSectionServiceを個別に生成"""
        return ManualSectionService()
