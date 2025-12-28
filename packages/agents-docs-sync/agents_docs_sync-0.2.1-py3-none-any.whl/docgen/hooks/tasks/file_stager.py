import os

from ..registry import TaskRegistry
from ..utils import run_command
from .base import HookContext, HookTask, TaskResult, TaskStatus


@TaskRegistry.register("stage_changes")
class FileStagerTask(HookTask):
    """ファイルステージングタスク"""

    def run(self, context: HookContext) -> TaskResult:
        # ステージング対象のファイルパターン（設定から取得、デフォルトはすべて）
        # ここではシンプルに変更されたファイルをすべて確認し、
        # 特定のファイル（ドキュメントなど）が含まれていればステージングするロジックにするか、
        # または単純に git add . するか（これは危険）。
        # 既存のフックでは特定のファイルのみを追加していた。

        target_files = self.config.params.get(
            "files", ["README.md", "AGENTS.md", "docs/api.md", "uv.lock"]
        )

        staged_files = []

        for file_path in target_files:
            abs_path = os.path.join(context.project_root, file_path)
            if not os.path.exists(abs_path):
                continue

            # 変更があるか確認（git status --porcelain）
            code, stdout, _ = run_command(
                ["git", "status", "--porcelain", file_path],
                cwd=context.project_root,
                capture_output=True,
            )

            if code == 0 and stdout.strip():
                # 変更あり、ステージング
                add_code, _, add_err = run_command(
                    ["git", "add", file_path], cwd=context.project_root
                )
                if add_code == 0:
                    staged_files.append(file_path)
                else:
                    print(f"Failed to stage {file_path}: {add_err}")

        if staged_files:
            return TaskResult(
                TaskStatus.SUCCESS,
                f"Staged files: {', '.join(staged_files)}",
                details={"files": staged_files},
            )
        else:
            return TaskResult(TaskStatus.SUCCESS, "No files to stage")
