"""
コミットメッセージ生成モジュール
LLMを使用してGitのコミットメッセージを自動生成
"""

from pathlib import Path
import subprocess
from typing import Any

from ..utils.exceptions import ErrorMessages
from ..utils.llm import LLMClientFactory
from ..utils.logger import get_logger
from ..utils.prompt_loader import PromptLoader


class CommitMessageGenerator:
    """コミットメッセージ生成クラス"""

    def __init__(self, project_root: Path, config: dict[str, Any]):
        """
        初期化

        Args:
            project_root: プロジェクトのルートディレクトリ
            config: 設定辞書
        """
        self.project_root = project_root
        self.config = config
        self.agents_config = config.get("agents", {})
        self.logger = get_logger("commit_message_generator")

    def generate(self) -> str | None:
        """
        コミットメッセージを生成

        Returns:
            生成されたコミットメッセージ（エラー時はNone）
        """
        try:
            # ステージング済みの変更を取得
            staged_changes = self._get_staged_changes()

            if not staged_changes:
                self.logger.warning("ステージング済みの変更がありません。")
                return None

            # LLMクライアントを取得
            llm_mode = self.agents_config.get("llm_mode", "api")
            preferred_mode = "api" if llm_mode in "api" else "local"

            client = LLMClientFactory.create_client_with_fallback(
                self.agents_config, preferred_mode=preferred_mode
            )

            if not client:
                self.logger.warning("LLMクライアントの作成に失敗しました。")
                return None

            # プロンプトを作成
            prompt = self._create_prompt(staged_changes)

            # システムプロンプト
            system_prompt = PromptLoader.load_system_prompt(
                "commit_message_prompts.toml", "generate", config=self.config
            )

            # LLMで生成
            self.logger.info("LLMを使用してコミットメッセージを生成中...")
            generated_message = client.generate(prompt, system_prompt=system_prompt)

            if generated_message:
                # 生成されたメッセージをクリーンアップ（改行を削除、先頭・末尾の空白を削除）
                message = generated_message.strip().split("\n")[0].strip()
                return message
            else:
                self.logger.warning("LLM生成が空でした。")
                return None

        except Exception as e:
            self.logger.error(f"コミットメッセージ生成中にエラーが発生しました: {e}", exc_info=True)
            return None

    def _get_staged_changes(self) -> str | None:
        """
        ステージング済みの変更を取得

        Returns:
            git diff --cachedの出力（エラー時はNone）
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--stat"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                self.logger.warning(f"git diff --cachedが失敗しました: {result.stderr}")
                return None

            # 統計情報とdiffの両方を取得
            stat_output = result.stdout

            # 詳細なdiffも取得
            diff_result = subprocess.run(
                ["git", "diff", "--cached"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False,
            )

            if diff_result.returncode == 0:
                # diffが長すぎる場合は最初の部分のみ
                diff_output = diff_result.stdout
                if len(diff_output) > 5000:
                    diff_output = diff_output[:5000] + "\n... (truncated)"
                return f"{stat_output}\n\n{diff_output}"
            else:
                return stat_output

        except FileNotFoundError:
            self.logger.error(ErrorMessages.GIT_COMMAND_NOT_FOUND)
            return None
        except Exception as e:
            self.logger.error(f"ステージング済みの変更の取得中にエラーが発生しました: {e}")
            return None

    def _create_prompt(self, staged_changes: str) -> str:
        """
        LLM用のプロンプトを作成

        Args:
            staged_changes: ステージング済みの変更内容

        Returns:
            プロンプト文字列
        """
        return PromptLoader.load_prompt(
            "commit_message_prompts.toml",
            "generate",
            config=self.config,
            staged_changes=staged_changes,
        )
