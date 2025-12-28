"""
アーキテクチャマニフェストのデータモデル
"""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
import yaml


class Module(BaseModel):
    """モジュール/パッケージ"""

    name: str
    path: Path
    is_package: bool = False
    dependencies: list[str] = Field(default_factory=list)
    submodules: list["Module"] = Field(default_factory=list)


class Service(BaseModel):
    """個別サービス/コンポーネント"""

    name: str
    type: str  # "python", "docker", "database", "external", etc.
    description: str | None = None
    ports: list[int] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    modules: list[Module] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ArchitectureManifest(BaseModel):
    """アーキテクチャマニフェスト"""

    project_name: str
    version: str = "1.0"
    services: list[Service] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_yaml(self, path: Path) -> None:
        """YAML形式で保存"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(self.model_dump(), f, allow_unicode=True, sort_keys=False)

    @classmethod
    def from_yaml(cls, path: Path) -> "ArchitectureManifest":
        """YAML形式から読み込み"""
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def deduplicate_services(
        self, preferred_languages: list[str] | None = None
    ) -> "ArchitectureManifest":
        """
        サービス重複除去と優先順位付け

        Args:
            preferred_languages: 優先する言語のリスト（languages.preferred設定）

        Returns:
            重複除去後のArchitectureManifest（selfを変更）
        """
        if not self.services:
            return self

        # サービス名でグループ化
        services_by_name: dict[str, list[Service]] = {}
        for service in self.services:
            if service.name not in services_by_name:
                services_by_name[service.name] = []
            services_by_name[service.name].append(service)

        # 各グループから最適なサービスを選択
        deduplicated: list[Service] = []
        for name, services_group in services_by_name.items():
            if len(services_group) == 1:
                # 重複がない場合はそのまま追加
                deduplicated.append(services_group[0])
            else:
                # 重複がある場合は最適なサービスを選択
                selected = self._select_best_service(services_group, preferred_languages)
                deduplicated.append(selected)

        self.services = deduplicated
        return self

    def _select_best_service(
        self, services: list[Service], preferred_languages: list[str] | None = None
    ) -> Service:
        """
        複数のサービスから最適なものを選択

        優先順位:
        1. 優先言語に一致するタイプのサービス
        2. より詳細な情報（モジュール、依存関係）を持つサービス
        3. 最初に見つかったサービス

        Args:
            services: 選択対象のサービスリスト
            preferred_languages: 優先する言語のリスト

        Returns:
            選択されたサービス
        """
        if len(services) == 1:
            return services[0]

        preferred_languages = preferred_languages or []

        # 優先言語に一致するサービスを探す
        for lang in preferred_languages:
            for service in services:
                if service.type == lang:
                    return service

        # より詳細な情報を持つサービスを優先
        def service_detail_score(service: Service) -> int:
            """サービスの詳細度スコア（高いほど詳細）"""
            score = 0
            if service.modules:
                score += len(service.modules) * 10
            if service.dependencies:
                score += len(service.dependencies) * 5
            if service.description:
                score += 1
            if service.ports:
                score += len(service.ports) * 2
            return score

        # スコアが最も高いサービスを選択
        best_service = max(services, key=service_detail_score)
        return best_service
