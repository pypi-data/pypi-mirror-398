"""
Base command class for CLI commands
"""

from abc import ABC, abstractmethod
from argparse import Namespace
from pathlib import Path


class BaseCommand(ABC):
    """コマンドハンドラーの基底クラス"""

    @abstractmethod
    def execute(self, args: Namespace, project_root: Path) -> int:
        """
        コマンドを実行

        Args:
            args: コマンドライン引数
            project_root: プロジェクトルートディレクトリ

        Returns:
            終了コード（0=成功、1=失敗）
        """
        pass
