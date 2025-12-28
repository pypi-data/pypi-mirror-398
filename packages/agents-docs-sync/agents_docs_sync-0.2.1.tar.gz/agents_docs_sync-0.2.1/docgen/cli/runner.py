"""
CLI Command Runner - Orchestrates command execution
"""

from argparse import Namespace
from pathlib import Path

from ..utils.logger import get_logger
from .commands import (
    BaseCommand,
    BenchmarkCommand,
    BuildIndexCommand,
    GenerateCommand,
    HooksCommand,
    InitCommand,
)

logger = get_logger("docgen.cli")


class CommandRunner:
    """コマンド実行を管理するオーケストレーター"""

    def __init__(self):
        # Command registry - maps command names to command classes
        self._commands: dict[str, type[BaseCommand]] = {
            "generate": GenerateCommand,
            "init": InitCommand,
            "build-index": BuildIndexCommand,
            "hooks": HooksCommand,
            "benchmark": BenchmarkCommand,
            "commit-msg": self._create_commit_msg_handler(),
            "arch": self._create_arch_handler(),
        }

    def run(self, args: Namespace, project_root: Path) -> int:
        """
        Execute the appropriate command based on parsed arguments

        Args:
            args: Parsed command line arguments
            project_root: Project root directory

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        # Determine which command to run
        command_name = self._determine_command(args)

        # Get the command class
        command_class = self._commands.get(command_name)
        if not command_class:
            logger.error(f"Unknown command: {command_name}")
            return 1

        # Special handling for build-index command - it needs config
        if command_name == "build-index":
            from .. import DocGen

            docgen = DocGen(project_root=project_root, config_path=getattr(args, "config", None))
            # Attach config to args for BuildIndexCommand
            args.config_dict = docgen.config

        # Execute the command
        try:
            if isinstance(command_class, type) and issubclass(command_class, BaseCommand):
                command = command_class()
                return command.execute(args, project_root)
            else:
                # Special handlers (commit-msg, arch)
                return command_class(args, project_root)
        except Exception as e:
            logger.error(f"Error executing command '{command_name}': {e}", exc_info=True)
            return 1

    def _determine_command(self, args: Namespace) -> str:
        """
        Determine which command to run from the arguments

        Args:
            args: Parsed arguments

        Returns:
            Command name
        """
        # Handle special flags that act as commands
        if getattr(args, "build_index", False):
            return "build-index"

        if getattr(args, "generate_arch", False):
            return "arch"

        # Use the command from subparsers, default to 'generate'
        command = getattr(args, "command", None)
        return command if command else "generate"

    def _create_commit_msg_handler(self):
        """Create a handler function for commit-msg command"""

        def commit_msg_handler(args: Namespace, project_root: Path) -> int:
            from typing import TYPE_CHECKING

            if TYPE_CHECKING:
                from ..generators.commit_message_generator import CommitMessageGenerator
            else:
                try:
                    from ..generators.commit_message_generator import CommitMessageGenerator
                except (ImportError, ValueError, SystemError):
                    from generators.commit_message_generator import CommitMessageGenerator  # type: ignore[no-redef]

            # DocGenの初期化が必要
            from .. import DocGen

            docgen = DocGen(project_root=project_root, config_path=getattr(args, "config", None))

            generator = CommitMessageGenerator(project_root, docgen.config)
            message = generator.generate()
            if message:
                print(message)
                return 0
            else:
                return 1

        return commit_msg_handler

    def _create_arch_handler(self):
        """Create a handler function for architecture generation"""

        def arch_handler(args: Namespace, project_root: Path) -> int:
            from .. import DocGen
            from ..archgen.cli import generate_architecture

            # DocGenを初期化して設定をロード
            docgen = DocGen(project_root=project_root, config_path=getattr(args, "config", None))

            # 設定から出力ディレクトリを取得
            arch_config = docgen.config.get("architecture", {})
            output_dir_str = arch_config.get("output_dir", "docs/architecture")
            output_dir = project_root / output_dir_str

            # 設定から除外ディレクトリを取得
            exclude_dirs = docgen.config.get("exclude", {}).get("directories", [])

            success = generate_architecture(
                project_root, output_dir, exclude_directories=exclude_dirs
            )
            return 0 if success else 1

        return arch_handler
