"""
Hooks command - Manage Git hooks
"""

from argparse import Namespace
from pathlib import Path
import shutil
import subprocess

from ...utils.exceptions import ErrorMessages
from ...utils.logger import get_logger
from .base import BaseCommand

logger = get_logger("docgen")


class HooksCommand(BaseCommand):
    """Git hooks管理コマンド"""

    def execute(self, args: Namespace, project_root: Path) -> int:
        """
        Handle Git hooks management actions

        Args:
            args: Command line arguments
            project_root: Project root directory

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        action = getattr(args, "hooks_action", None)

        if action == "run":
            return self._handle_run(args)

        git_hooks_dir = project_root / ".git" / "hooks"
        docgen_hooks_dir = project_root / "docgen" / "hooks"

        if not docgen_hooks_dir.exists():
            logger.error(ErrorMessages.HOOKS_DIR_NOT_FOUND)
            return 1

        if action == "list":
            return self._handle_list(project_root)

        elif action == "validate":
            return self._handle_validate(project_root)

        hook_names = ["pre-commit", "post-commit", "pre-push", "commit-msg"]
        target_hooks = (
            [getattr(args, "hook_name", None)] if getattr(args, "hook_name", None) else hook_names
        )

        if action == "enable":
            return self._enable_hooks(git_hooks_dir, docgen_hooks_dir, target_hooks)
        elif action == "disable":
            return self._disable_hooks(git_hooks_dir, target_hooks)
        else:
            logger.error(f"Unknown action: {action}")
            return 1

    def _handle_run(self, args: Namespace) -> int:
        """Handle 'run' action"""
        try:
            from ...hooks.orchestrator import HookOrchestrator

            hook_name = getattr(args, "hook_name", None)
            hook_args = getattr(args, "hook_args", [])

            if hook_name is None:
                raise ValueError("hook_name is required")
            orchestrator = HookOrchestrator(hook_name, hook_args)

            # Register tasks
            from ...hooks.tasks.commit_msg_generator import CommitMsgGeneratorTask
            from ...hooks.tasks.doc_generator import DocGeneratorTask
            from ...hooks.tasks.file_stager import FileStagerTask
            from ...hooks.tasks.rag_generator import RagGeneratorTask
            from ...hooks.tasks.test_runner import TestRunnerTask
            from ...hooks.tasks.version_checker import VersionCheckerTask

            orchestrator.register_task("run_tests", TestRunnerTask)
            orchestrator.register_task("generate_docs", DocGeneratorTask)
            orchestrator.register_task("generate_rag", RagGeneratorTask)
            orchestrator.register_task("stage_changes", FileStagerTask)
            orchestrator.register_task("generate_commit_message", CommitMsgGeneratorTask)
            orchestrator.register_task("check_version", VersionCheckerTask)

            return orchestrator.run()
        except ImportError as e:
            logger.error(f"Failed to load hook orchestrator: {e}")
            return 1

    def _handle_list(self, project_root: Path) -> int:
        """Handle 'list' action"""
        print("\nAvailable Git hooks:")
        print(f"  Config file: {project_root}/docgen/hooks.toml")
        print("-" * 40)

        try:
            from ...hooks.config import ConfigLoader

            loader = ConfigLoader(str(project_root))
            hooks = loader.load_config()
            for name, hook_config in hooks.items():
                status = "Enabled" if hook_config.enabled else "Disabled"
                print(f"  {name}: {status}")
                for task in hook_config.tasks:
                    task_status = "Enabled" if task.enabled else "Disabled"
                    print(f"    - {task.name}: {task_status}")
        except Exception as e:
            print(f"  Config load error: {e}")
        print("-" * 40)
        return 0

    def _handle_validate(self, project_root: Path) -> int:
        """Handle 'validate' action"""
        print("Validating hook config...")
        try:
            from ...hooks.config import ConfigLoader

            loader = ConfigLoader(str(project_root))
            config = loader.load_config()
            print("✓ Config file is valid TOML")
            print(f"✓ Found {len(config)} hook definitions")
            return 0
        except Exception as e:
            print(f"✗ Validation error: {e}")
            return 1

    def _enable_hooks(self, git_hooks_dir, docgen_hooks_dir, hook_names):
        """Enable hooks"""

        git_hooks_dir.mkdir(parents=True, exist_ok=True)

        for hook_name in hook_names:
            source_file = docgen_hooks_dir / hook_name
            hook_file = git_hooks_dir / hook_name

            if not source_file.exists():
                logger.warning(
                    ErrorMessages.HOOK_SOURCE_NOT_FOUND.format(
                        hook_name=hook_name, source_file=source_file
                    )
                )
                continue

            # Backup existing hook
            if hook_file.exists() and not self._is_docgen_hook(hook_file):
                backup_file = hook_file.with_suffix(
                    f"{hook_file.suffix}.backup.{subprocess.run(['date', '+%Y%m%d_%H%M%S'], capture_output=True, text=True).stdout.strip()}"
                )
                shutil.copy2(hook_file, backup_file)
                logger.info(f"Backed up existing {hook_name} hook: {backup_file}")

            # Add hook
            if not self._is_docgen_hook(hook_file):
                with open(hook_file, "a") as f:
                    if not hook_file.exists() or not self._has_shebang(hook_file):
                        f.write("#!/bin/bash\n")
                    f.write(f"\n# docgen - {hook_name} hook\n")
                    with open(source_file) as src:
                        f.write(src.read())
                hook_file.chmod(0o755)
                logger.info(f"✓ Installed {hook_name} hook")
            else:
                logger.info(f"✓ {hook_name} hook is already installed")

        logger.info("Enabled Git hooks")
        return 0

    def _disable_hooks(self, git_hooks_dir, hook_names):
        """Disable hooks"""

        for hook_name in hook_names:
            hook_file = git_hooks_dir / hook_name
            disabled_file = hook_file.with_suffix(f"{hook_file.suffix}.disabled")

            if hook_file.exists():
                if self._is_docgen_hook(hook_file):
                    shutil.move(hook_file, disabled_file)
                    logger.info(f"✓ Disabled {hook_name} hook")
                else:
                    logger.info(f"✓ {hook_name} hook is not a docgen hook (ignored)")
            else:
                logger.info(f"✓ {hook_name} hook does not exist")

        logger.info("Disabled Git hooks")
        return 0

    def _is_docgen_hook(self, hook_file):
        """Check if hook file is a docgen hook"""
        try:
            with open(hook_file) as f:
                return "# docgen" in f.read()
        except FileNotFoundError:
            return False

    def _has_shebang(self, hook_file):
        """Check if hook file has a shebang"""
        try:
            with open(hook_file) as f:
                first_line = f.readline().strip()
                return first_line.startswith("#!")
        except FileNotFoundError:
            return False
