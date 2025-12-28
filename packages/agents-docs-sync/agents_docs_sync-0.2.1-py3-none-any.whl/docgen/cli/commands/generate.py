"""
Generate command - Generate documentation
"""

from argparse import Namespace
from pathlib import Path

from ...utils.logger import get_logger
from .base import BaseCommand

logger = get_logger("docgen")


class GenerateCommand(BaseCommand):
    """ドキュメント生成コマンド"""

    def execute(self, args: Namespace, project_root: Path) -> int:
        """
        Generate documentation

        Args:
            args: Command line arguments
            project_root: Project root directory

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        from ... import DocGen

        # Initialize DocGen
        config_path = getattr(args, "config", None)
        docgen = DocGen(project_root=project_root, config_path=config_path)

        # Handle detect-only mode
        if getattr(args, "detect_only", False):
            languages = docgen.detect_languages()
            lang_names = [lang.name for lang in languages]
            logger.info(f"\n検出された言語: {', '.join(lang_names) if lang_names else 'なし'}")
            return 0

        # Update configuration based on arguments
        config_updates = {}

        if getattr(args, "no_api_doc", False):
            config_updates["generation.generate_api_doc"] = False

        if getattr(args, "no_readme", False):
            config_updates["generation.update_readme"] = False

        if getattr(args, "use_rag", False):
            config_updates["rag.enabled"] = True

        if config_updates:
            docgen.update_config(config_updates)

        # Generate documents
        if docgen.generate_documents():
            return 0
        else:
            return 1
