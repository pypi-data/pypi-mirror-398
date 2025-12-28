"""
プロジェクトスキャナー
"""

from pathlib import Path
from typing import Any

from .detectors.docker_detector import DockerDetector
from .detectors.generic_detector import GenericDetector
from .detectors.python_detector import PythonDetector
from .models import ArchitectureManifest


class ProjectScanner:
    """プロジェクトをスキャンしてアーキテクチャを抽出"""

    def __init__(
        self,
        project_root: Path,
        exclude_directories: list[str] | None = None,
        config: dict[str, Any] | None = None,
    ):
        """
        初期化

        Args:
            project_root: プロジェクトルートディレクトリ
            exclude_directories: 除外するディレクトリのリスト
            config: 設定辞書（依存関係フィルタリング用）
        """
        self.project_root = project_root
        self.config = config or {}

        # 依存関係の除外パターンを構築
        self.exclude_patterns = self._build_exclude_patterns()

        self.detectors = [
            PythonDetector(
                exclude_directories=exclude_directories, exclude_patterns=self.exclude_patterns
            ),
            GenericDetector(
                exclude_directories=exclude_directories, exclude_patterns=self.exclude_patterns
            ),
            DockerDetector(),
        ]

    def _build_exclude_patterns(self) -> set[str]:
        """
        依存関係の除外パターンを構築

        Returns:
            除外パターンのセット
        """
        exclude_patterns = set()

        # 1. プロジェクト名を除外
        project_name = self.project_root.name
        if project_name:
            exclude_patterns.add(project_name)
            # ハイフンをアンダースコアに変換したバージョンも除外
            exclude_patterns.add(project_name.replace("-", "_"))
            exclude_patterns.add(project_name.replace("_", "-"))

        # 2. exclude.directories の各ディレクトリ名を除外
        exclude_config = self.config.get("exclude", {})
        exclude_directories = exclude_config.get("directories", [])
        for dir_name in exclude_directories:
            if dir_name:
                exclude_patterns.add(dir_name)
                # ハイフン/アンダースコアの変換も考慮
                exclude_patterns.add(dir_name.replace("-", "_"))
                exclude_patterns.add(dir_name.replace("_", "-"))

        # 3. languages.ignored の言語名を除外（一般的なツール名として）
        languages_config = self.config.get("languages", {})
        ignored_languages = languages_config.get("ignored", [])
        for lang in ignored_languages:
            if lang:
                exclude_patterns.add(lang)

        # 4. 一般的なツール名を除外（docgen, agents-docs-sync など）
        common_tool_names = ["docgen", "agents-docs-sync", "agents_docs_sync"]
        for tool_name in common_tool_names:
            exclude_patterns.add(tool_name)
            exclude_patterns.add(tool_name.replace("-", "_"))
            exclude_patterns.add(tool_name.replace("_", "-"))

        # 5. プロジェクトルート直下のディレクトリ名を除外（主要なモジュール名として）
        try:
            for item in self.project_root.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    exclude_patterns.add(item.name)
                    exclude_patterns.add(item.name.replace("-", "_"))
                    exclude_patterns.add(item.name.replace("_", "-"))
        except Exception:
            pass

        return exclude_patterns

    def scan(self) -> ArchitectureManifest:
        """
        プロジェクトをスキャン

        Returns:
            アーキテクチャマニフェスト（サービス重複除去済み）
        """
        services = []
        for detector in self.detectors:
            if hasattr(detector, "detect"):
                detected = detector.detect(self.project_root)  # type: ignore[attr-defined]
                services.extend(detected)

        manifest = ArchitectureManifest(project_name=self.project_root.name, services=services)

        # サービス重複除去と優先順位付けを自動実行
        preferred_languages = self.config.get("languages", {}).get("preferred", [])
        manifest.deduplicate_services(preferred_languages=preferred_languages)

        return manifest
