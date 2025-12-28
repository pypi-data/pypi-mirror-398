import os

from ..registry import TaskRegistry
from ..utils import get_python_command, run_command
from .base import HookContext, HookTask, TaskResult, TaskStatus


@TaskRegistry.register("generate_commit_message")
class CommitMsgGeneratorTask(HookTask):
    """コミットメッセージ生成タスク"""

    def run(self, context: HookContext) -> TaskResult:
        commit_msg_file = context.args[0] if context.args else None

        if not commit_msg_file:
            return TaskResult(TaskStatus.FAILURE, "No commit message file provided")

        # 既存のメッセージを確認
        if self.config.params.get("only_if_empty", True):
            if os.path.exists(commit_msg_file):
                with open(commit_msg_file) as f:
                    content = f.read().strip()
                    # コメント行を除外してチェック
                    lines = [
                        line for line in content.splitlines() if not line.strip().startswith("#")
                    ]
                    if any(lines):
                        return TaskResult(TaskStatus.SKIPPED, "Commit message already exists")

        print("Generating commit message...")

        python_cmd = get_python_command()
        # docgen commit-msg コマンドを実行
        cmd = python_cmd.split() + ["-m", "docgen.docgen", "commit-msg"]

        code, stdout, stderr = run_command(cmd, cwd=context.project_root, capture_output=True)

        if code == 0 and stdout.strip():
            msg = stdout.strip()
            # ファイルに書き込み
            with open(commit_msg_file, "w") as f:
                f.write(msg)
            return TaskResult(
                TaskStatus.SUCCESS, "Commit message generated", details={"message": msg}
            )
        else:
            return TaskResult(
                TaskStatus.FAILURE,
                "Failed to generate commit message",
                details={"stdout": stdout, "stderr": stderr},
            )
