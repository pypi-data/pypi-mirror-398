import os

from ..registry import TaskRegistry
from ..utils import run_command
from .base import HookContext, HookTask, TaskResult, TaskStatus


@TaskRegistry.register("run_tests")
class TestRunnerTask(HookTask):
    """テスト実行タスク"""

    def run(self, context: HookContext) -> TaskResult:
        script_path = os.path.join(context.project_root, "scripts", "run_tests.sh")

        if not os.path.exists(script_path):
            return TaskResult(TaskStatus.FAILURE, f"Test script not found: {script_path}")

        # 実行権限を確認・付与
        if not os.access(script_path, os.X_OK):
            os.chmod(script_path, 0o755)

        print("Running tests...")

        # タイムアウト設定（デフォルト300秒）
        # timeout = self.config.timeout or 300

        try:
            # subprocess.runを使って直接実行（リアルタイム出力は難しいが、結果は取得可能）
            # 実際の出力を見せるために、capture_output=Falseにする手もあるが、
            # ここではログ収集のためにcapture_output=Trueとし、失敗時にstderrを表示する

            # 注: ユーザー体験向上のため、テスト実行中は出力を表示したい場合が多い
            # その場合は subprocess.Popen を使うか、capture_output=False にする
            # ここではシンプルに実行し、失敗時のみ詳細を表示する方針とする

            code, stdout, stderr = run_command([script_path], cwd=context.project_root)

            if code == 0:
                return TaskResult(TaskStatus.SUCCESS, "All tests passed")
            else:
                return TaskResult(
                    TaskStatus.FAILURE, "Tests failed", details={"stdout": stdout, "stderr": stderr}
                )

        except Exception as e:
            return TaskResult(TaskStatus.FAILURE, f"Error running tests: {str(e)}")
