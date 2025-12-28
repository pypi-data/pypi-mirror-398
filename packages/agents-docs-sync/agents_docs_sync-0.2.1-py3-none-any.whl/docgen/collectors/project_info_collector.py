"""
プロジェクト情報収集モジュール
ビルド/テスト手順、コーディング規約、依存関係などの情報を収集
"""

from pathlib import Path
from typing import Any

from ..models.project import ProjectInfo
from ..utils.logger import get_logger
from .collector_utils import BuildCommandCollector


class ProjectInfoCollector:
    """プロジェクト情報収集クラス

    プロジェクトのビルド/テスト手順、依存関係、コーディング規約などを収集する。
    """

    # ファイルパス定数
    GITHUB_WORKFLOWS_DIR = ".github/workflows"

    def __init__(
        self,
        project_root: Path,
        package_managers: dict[str, str] | None = None,
        logger: Any | None = None,
        exclude_directories: list[str] | None = None,
    ):
        """
        初期化

        Args:
            project_root: プロジェクトのルートディレクトリ
            package_managers: 言語ごとのパッケージマネージャ辞書
            logger: ロガーインスタンス
            exclude_directories: 除外するディレクトリのリスト
        """
        self.project_root: Path = project_root
        self.package_managers = package_managers or {}
        self.logger = logger or get_logger(__name__)

        # Initialize sub-collectors
        from .coding_standards_collector import CodingStandardsCollector
        from .collector_utils import TestingCommandScanner
        from .dependency_collector import DependencyCollector
        from .language_info_collector import LanguageInfoCollector
        from .structure_analyzer import StructureAnalyzer

        self.build_collector = BuildCommandCollector(project_root, package_managers)
        self.dependency_collector = DependencyCollector(project_root, logger=self.logger)
        self.test_command_collector = TestingCommandScanner(
            project_root, package_managers, logger=self.logger
        )
        self.coding_standards_collector = CodingStandardsCollector(project_root, logger=self.logger)
        self.structure_analyzer = StructureAnalyzer(
            project_root, logger=self.logger, exclude_directories=exclude_directories
        )
        self.language_info_collector = LanguageInfoCollector(project_root, logger=self.logger)

    def collect_all(self) -> ProjectInfo:
        """
        すべてのプロジェクト情報を収集

        Returns:
            プロジェクト情報の辞書
        """
        self.logger.info("Collecting project information...")

        # 各情報を収集
        dependencies = self.collect_dependencies()
        test_commands = self.collect_test_commands()
        build_commands = self.build_collector.collect_build_commands()
        coding_standards = self.collect_coding_standards()
        project_structure = self.collect_project_structure()

        # LanguageInfoCollectorから情報を取得
        lang_info = self.language_info_collector.collect()
        project_description = lang_info["description"]
        scripts = lang_info["scripts"]

        key_features = self.collect_key_features()
        ci_cd_info = self.collect_ci_cd_info()

        return ProjectInfo(
            dependencies=dependencies,
            test_commands=test_commands,
            build_commands=build_commands,
            coding_standards=coding_standards,
            project_structure=project_structure,
            description=project_description,
            key_features=key_features,
            ci_cd_info=ci_cd_info,
            scripts=scripts,
        )

    def collect_key_features(self) -> list[str]:
        """
        主要機能を収集（プレースホルダー）

        Returns:
            主要機能のリスト
        """
        # TODO: 実装
        return []

    def collect_test_commands(self) -> list[str]:
        """
        テストコマンドを収集

        Returns:
            テストコマンドのリスト
        """
        return self.test_command_collector.collect_test_commands()

    def collect_dependencies(self) -> dict[str, list[str]]:
        """
        依存関係を収集

        Returns:
            依存関係の辞書（言語ごと）
        """
        return self.dependency_collector.collect_dependencies()

    def collect_coding_standards(self) -> dict[str, str | dict[str, Any] | bool]:
        """
        コーディング規約を収集

        Returns:
            コーディング規約の辞書
        """
        return self.coding_standards_collector.collect_coding_standards()

    def collect_ci_cd_info(self) -> dict[str, Any]:
        """
        CI/CD情報を収集

        Returns:
            CI/CD情報の辞書
        """
        ci_cd_info = {}

        # GitHub Actions
        github_workflows = self.project_root / self.GITHUB_WORKFLOWS_DIR
        if github_workflows.exists() and github_workflows.is_dir():
            workflows = []
            for item in github_workflows.iterdir():
                if item.suffix in [".yml", ".yaml"]:
                    workflows.append(item.name)
            if workflows:
                ci_cd_info["github_actions"] = workflows

        return ci_cd_info

    def collect_project_structure(self) -> dict[str, Any]:
        """
        プロジェクト構造を収集

        StructureAnalyzerに委譲して詳細な構造分析を実行

        Returns:
            プロジェクト構造の辞書
        """
        return self.structure_analyzer.analyze()
