"""
Base Collector Module
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ..utils.logger import get_logger


class BaseCollector[T](ABC):
    """ベースコレクタークラス

    Generic[T]を使用して、各collectorが返す型を明示的に定義可能にする。

    Type Parameters:
        T: このコレクターが収集して返すデータの型
    """

    def __init__(self, project_root: Path, logger: Any | None = None):
        """
        初期化

        Args:
            project_root: プロジェクトのルートディレクトリ
            logger: ロガーインスタンス（Noneの場合はデフォルトロガーを使用）
        """
        self.project_root = project_root
        self.logger = logger or get_logger(self.__class__.__name__.lower())

    @abstractmethod
    def collect(self) -> T:
        """
        情報を収集（サブクラスで実装）

        Returns:
            収集した情報（型Tのインスタンス）
        """
        pass
