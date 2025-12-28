import logging
from pathlib import Path
import sys
import time
from typing import Any

from docgen.utils.exceptions import HookError

from .config import ConfigLoader, TaskConfig
from .tasks.base import HookContext, TaskStatus

# ロガー設定
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


import asyncio


class HookOrchestrator:
    """Git hook実行のオーケストレーター"""

    def __init__(self, hook_name: str, args: list[str] | None = None):
        self.hook_name = hook_name
        self.args = args or []
        self.project_root = self._find_project_root()
        self.config_loader = ConfigLoader(str(self.project_root))
        self.hooks_config = self.config_loader.load_config()
        self.task_registry: dict[str, Any] = {}

    def _find_project_root(self) -> Path:
        """プロジェクトルートを見つける"""
        # 現在のディレクトリから親を辿って.gitを探す
        current = Path.cwd()
        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent
        return Path.cwd()  # フォールバック

    def register_task(self, name: str, task_class: type):
        """タスクを登録する"""
        self.task_registry[name] = task_class

    async def run_async(self) -> int:
        """フックを非同期実行する"""
        hook_config = self.hooks_config.get(self.hook_name)

        # 設定がない、または無効な場合は何もしない（成功扱い）
        if not hook_config or not hook_config.enabled:
            return 0

        logger.info(f"Running git hook: {self.hook_name}")

        context = HookContext(
            project_root=str(self.project_root), hook_name=self.hook_name, args=self.args
        )

        success = True

        # 依存関係のないタスクを並列実行するための準備
        # 現在は単純に順番にawaitしているが、将来的には依存関係解析を入れて並列化する
        # TODO: 依存関係解析と並列実行の実装

        for task_config in hook_config.tasks:
            if not task_config.enabled:
                continue

            try:
                if not await self._run_task_async(task_config, context):
                    success = False
                    if not task_config.continue_on_error:
                        logger.error(f"Hook failed at task: {task_config.name}")
                        return 1
            except HookError as e:
                logger.error(f"  ✗ {task_config.name} error: {e}")
                success = False
                if not task_config.continue_on_error:
                    return 1

        return 0 if success else 1

    async def _run_task_async(self, config: TaskConfig, context: HookContext) -> bool:
        """個別タスクを非同期実行する"""
        task_class = self.task_registry.get(config.name)
        if not task_class:
            logger.warning(f"Unknown task: {config.name}")
            return True

        try:
            task = task_class(config)

            if not task.should_run(context):
                return True

            logger.info(f"  Running task: {config.name}...")
            start_time = time.time()

            # 非同期実行
            result = await task.run_async(context)

            duration = time.time() - start_time

            if result.status == TaskStatus.SUCCESS:
                logger.info(f"  ✓ {config.name} passed ({duration:.2f}s)")
                return True
            elif result.status == TaskStatus.SKIPPED:
                logger.info(f"  - {config.name} skipped")
                return True
            else:
                logger.error(f"  ✗ {config.name} failed: {result.message}")
                return False

        except HookError:
            raise
        except Exception as e:
            raise HookError(
                message="タスク実行時にエラーが発生しました",
                hook_name=config.name,
                details=str(e),
            ) from e

    def run(self) -> int:
        """同期実行ラッパー"""
        return asyncio.run(self.run_async())


def main():
    """エントリーポイント"""
    if len(sys.argv) < 2:
        print("Usage: python -m docgen.hooks.orchestrator <hook_name> [args...]")
        sys.exit(1)

    hook_name = sys.argv[1]
    args = sys.argv[2:]

    # タスクモジュールをインポートして登録を実行
    from . import tasks  # noqa: F401
    from .registry import TaskRegistry

    orchestrator = HookOrchestrator(hook_name, args)
    orchestrator.task_registry = TaskRegistry.get_all_tasks()

    sys.exit(orchestrator.run())


if __name__ == "__main__":
    main()
