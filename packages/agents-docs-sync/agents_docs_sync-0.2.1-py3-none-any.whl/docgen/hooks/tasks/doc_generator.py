from ..registry import TaskRegistry
from ..utils import get_python_command, run_command
from .base import HookContext, HookTask, TaskResult, TaskStatus


@TaskRegistry.register("generate_docs")
class DocGeneratorTask(HookTask):
    """ドキュメント生成タスク"""

    def run(self, context: HookContext) -> TaskResult:
        print("Generating documentation...")

        python_cmd = get_python_command()
        cmd = python_cmd.split() + ["-m", "docgen.docgen"]

        # 設定ファイルパス
        # config_path = os.path.join(context.project_root, "docgen", "config.toml")

        # 一時的にLLMモードをtemplateに変更するための環境変数を設定することも考えられるが、
        # 現在のdocgen.pyは環境変数でのオーバーライドを完全にはサポートしていない可能性がある。
        # 代わりに、docgen.py自体がCI環境（TTYなし）を検知して挙動を変えるか、
        # 引数でモードを指定できるようにするのが理想的。
        # ここでは既存のフックと同様に、設定ファイルを一時的に書き換えるのはリスクがあるため、
        # そのまま実行するか、将来的にdocgen.pyにフラグを追加することを想定する。

        # 既存のpre-commitフックではsedでconfig.tomlを書き換えていたが、
        # それはあまり行儀が良くない。
        # 今回はそのまま実行する（docgen側で適切に処理されることを期待、または後でdocgenを改修）

        code, stdout, stderr = run_command(cmd, cwd=context.project_root)

        if code == 0:
            return TaskResult(TaskStatus.SUCCESS, "Documentation generated successfully")
        else:
            return TaskResult(
                TaskStatus.FAILURE,
                "Documentation generation failed",
                details={"stdout": stdout, "stderr": stderr},
            )
