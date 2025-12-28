import os
import re

from ..registry import TaskRegistry
from ..utils import run_command
from .base import HookContext, HookTask, TaskResult, TaskStatus


@TaskRegistry.register("check_version")
class VersionCheckerTask(HookTask):
    """バージョンチェック＆リリースタグ作成タスク"""

    def run(self, context: HookContext) -> TaskResult:
        pyproject_path = os.path.join(context.project_root, "pyproject.toml")
        if not os.path.exists(pyproject_path):
            return TaskResult(TaskStatus.SKIPPED, "pyproject.toml not found")

        # ローカルバージョン取得
        local_version = self._get_version(pyproject_path)
        if not local_version:
            return TaskResult(TaskStatus.FAILURE, "Could not determine local version")

        # リモートバージョン取得（git show）
        # 注意: リモートブランチ名は動的に取得する必要があるが、ここでは origin/main を仮定、
        # または upstream を確認するロジックが必要

        # 簡易的に、pyproject.tomlが変更されているかだけで判断する（既存フックのロジック）
        code, _, _ = run_command(
            ["git", "diff", "--quiet", "HEAD@{upstream}", "--", "pyproject.toml"],
            cwd=context.project_root,
        )

        if code == 0:
            return TaskResult(TaskStatus.SKIPPED, "Version not changed")

        # バージョン変更あり
        print(f"Version change detected: {local_version}")

        # 自動確認設定
        auto_confirm = self.config.params.get("auto_confirm", False)
        interactive = self.config.params.get("interactive", True)

        if not auto_confirm and interactive:
            # インタラクティブモード（CLI実行時のみ有効、Gitフック内では注意が必要）
            # input() はTTYが必要
            try:
                response = input(f"Create release tag v{local_version}? [y/N] ")
                if response.lower() != "y":
                    return TaskResult(TaskStatus.SKIPPED, "Tag creation cancelled by user")
            except EOFError:
                # TTYがない場合など
                return TaskResult(TaskStatus.SKIPPED, "Cannot ask for confirmation (no TTY)")

        # タグ作成
        tag_name = f"v{local_version}"

        # 既存タグチェック
        code, _, _ = run_command(["git", "rev-parse", tag_name], cwd=context.project_root)
        if code == 0:
            return TaskResult(TaskStatus.SKIPPED, f"Tag {tag_name} already exists")

        # タグ作成実行
        code, _, err = run_command(
            ["git", "tag", "-a", tag_name, "-m", f"Release version {local_version}"],
            cwd=context.project_root,
        )

        if code != 0:
            return TaskResult(TaskStatus.FAILURE, f"Failed to create tag: {err}")

        # タグプッシュ
        code, _, err = run_command(["git", "push", "origin", tag_name], cwd=context.project_root)

        if code != 0:
            return TaskResult(TaskStatus.FAILURE, f"Failed to push tag: {err}")

        return TaskResult(TaskStatus.SUCCESS, f"Created and pushed tag {tag_name}")

    def _get_version(self, file_path: str) -> str:
        try:
            with open(file_path) as f:
                content = f.read()
                match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
                if match:
                    return match.group(1)
        except Exception:
            pass
        return ""
