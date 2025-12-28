from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..config import TaskConfig


class TaskStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    SKIPPED = "skipped"


@dataclass
class TaskResult:
    status: TaskStatus
    message: str = ""
    details: dict[str, Any] | None = None


@dataclass
class HookContext:
    project_root: str
    hook_name: str
    args: list[str]


class HookTask(ABC):
    """フックタスクの基底クラス"""

    def __init__(self, config: TaskConfig):
        self.config = config

    @abstractmethod
    def run(self, context: HookContext) -> TaskResult:
        """タスクを実行"""
        pass

    def should_run(self, context: HookContext) -> bool:
        """タスクを実行すべきか判定"""
        return True

    async def run_async(self, context: HookContext) -> TaskResult:
        """タスクを非同期実行（デフォルトは同期実行をラップ）"""
        return self.run(context)
