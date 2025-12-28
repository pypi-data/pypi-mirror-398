from ..registry import TaskRegistry
from ..utils import get_python_command, run_command
from .base import HookContext, HookTask, TaskResult, TaskStatus


@TaskRegistry.register("generate_rag")
class RagGeneratorTask(HookTask):
    """RAG生成タスク"""

    def run(self, context: HookContext) -> TaskResult:
        print("Updating RAG vector database...")

        # RAG機能が有効か確認（config.tomlなどをチェックすべきだが、
        # ここではタスクが有効化されている＝実行すべきと判断）

        python_cmd = get_python_command()
        # RAG生成コマンド（仮: docgen rag update または専用スクリプト）
        # 現時点では専用のエントリーポイントがない可能性があるため、
        # 将来的に docgen.py に rag サブコマンドを追加することを想定
        # または、直接モジュールを実行する

        # docgen.py の --build-index オプションを使用
        cmd = python_cmd.split() + ["-m", "docgen.docgen", "--build-index"]

        try:
            code, stdout, stderr = run_command(cmd, cwd=context.project_root, capture_output=True)

            if code == 0:
                return TaskResult(TaskStatus.SUCCESS, "RAG vector database updated")
            else:
                # RAGモジュールがまだない、またはエラー
                # continue_on_error: true が推奨されるため、失敗情報を返す
                return TaskResult(
                    TaskStatus.FAILURE,
                    "RAG update failed",
                    details={"stdout": stdout, "stderr": stderr},
                )
        except Exception as e:
            return TaskResult(TaskStatus.FAILURE, f"Error updating RAG: {str(e)}")
