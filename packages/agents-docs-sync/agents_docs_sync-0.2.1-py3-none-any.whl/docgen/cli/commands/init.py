"""
Init command - Initialize the project
"""

from argparse import Namespace
from pathlib import Path
import shutil

from ...utils.logger import get_logger
from .base import BaseCommand

# Define constants locally to avoid circular import
DOCGEN_DIR = Path(__file__).parent.parent.parent.resolve()

logger = get_logger("docgen")


class InitCommand(BaseCommand):
    """プロジェクト初期化コマンド"""

    def execute(self, args: Namespace, project_root: Path) -> int:
        """
        Initialize the project

        Args:
            args: Command line arguments
            project_root: Project root directory

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        force = getattr(args, "force", False)
        quiet = getattr(args, "quiet", False)

        docgen_dir = project_root / "docgen"
        config_file = docgen_dir / "config.toml"

        # Check existing files
        if config_file.exists() and not force:
            logger.warning(
                f"Config file already exists: {config_file}\nUse --force flag to overwrite."
            )
            return 1

        # Create docgen directory
        docgen_dir.mkdir(parents=True, exist_ok=True)

        # Source directory in package
        package_docgen_dir = DOCGEN_DIR

        try:
            # 1. Copy config.toml.sample to config.toml
            source_config = package_docgen_dir / "config.toml.sample"
            if source_config.exists():
                shutil.copy2(source_config, config_file)
                if not quiet:
                    logger.info(f"✓ Created config file: {config_file}")
            else:
                logger.error(f"Source file not found: {source_config}")
                return 1

            # 2. Copy templates directory
            self._copy_directory_contents(
                package_docgen_dir / "templates",
                docgen_dir / "templates",
                quiet=quiet,
                description="Templates",
            )

            # 3. Copy prompts directory
            self._copy_directory_contents(
                package_docgen_dir / "prompts",
                docgen_dir / "prompts",
                quiet=quiet,
                description="Prompts",
            )

            # 4. Copy hooks directory (with execution permissions)
            hooks_copied = self._copy_directory_contents(
                package_docgen_dir / "hooks",
                docgen_dir / "hooks",
                quiet=quiet,
                description="Git hooks",
            )

            # Grant execution permissions to hooks files
            if hooks_copied:
                hooks_dir = docgen_dir / "hooks"
                for hook_file in hooks_dir.iterdir():
                    if hook_file.is_file():
                        hook_file.chmod(0o755)

            if not quiet:
                logger.info("✓ Project initialization completed")

            return 0

        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            return 1

    def _copy_directory_contents(
        self, source_dir: Path, dest_dir: Path, quiet: bool = False, description: str = "Files"
    ) -> bool:
        """Copy directory contents"""
        if not source_dir.exists():
            logger.warning(f"Source directory not found: {source_dir}")
            return False

        dest_dir.mkdir(parents=True, exist_ok=True)

        try:
            for item in source_dir.iterdir():
                if item.is_file():
                    shutil.copy2(item, dest_dir / item.name)

            if not quiet:
                file_count = len(list(dest_dir.iterdir()))
                logger.info(f"✓ Copied {description}: {file_count} files")

            return True

        except Exception as e:
            logger.error(f"Error copying {description}: {e}")
            return False
