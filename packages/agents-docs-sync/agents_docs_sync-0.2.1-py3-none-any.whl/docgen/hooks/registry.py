from .tasks.base import HookTask


class TaskRegistry:
    """フックタスクのレジストリ"""

    _registry: dict[str, type[HookTask]] = {}

    @classmethod
    def register(cls, name: str):
        """タスクを登録するデコレータ"""

        def wrapper(task_class: type[HookTask]):
            cls._registry[name] = task_class
            return task_class

        return wrapper

    @classmethod
    def get_task(cls, name: str) -> type[HookTask] | None:
        """タスククラスを取得"""
        return cls._registry.get(name)

    @classmethod
    def get_all_tasks(cls) -> dict[str, type[HookTask]]:
        """全タスクを取得"""
        return cls._registry.copy()
