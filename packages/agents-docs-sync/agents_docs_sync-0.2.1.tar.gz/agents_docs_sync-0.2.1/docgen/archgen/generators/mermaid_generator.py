"""
Mermaid.js 形式のアーキテクチャ図生成器
"""

from pathlib import Path
from typing import Any

from ..models import ArchitectureManifest


class MermaidGenerator:
    """Mermaid.js形式でアーキテクチャ図を生成（依存なし）"""

    # タイプごとのアイコン（Mermaid font-awesome対応）
    TYPE_ICONS = {
        "python": "fa:fa-python",
        "docker": "fa:fa-docker",
        "database": "fa:fa-database",
        "api": "fa:fa-server",
        "external": "fa:fa-cloud",
    }

    def generate(self, manifest: ArchitectureManifest, output_dir: Path) -> Path:
        """Mermaid形式のアーキテクチャ図を生成"""
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "architecture.mmd"

        mermaid_code = self._generate_mermaid(manifest)

        # .mmd ファイルとして保存
        output_path.write_text(mermaid_code, encoding="utf-8")

        # Markdown埋め込み形式も生成
        md_path = output_dir / "architecture_diagram.md"
        md_content = f"""# {manifest.project_name} Architecture

```mermaid
{mermaid_code}
```

## Services

{self._generate_service_list(manifest)}
"""
        md_path.write_text(md_content, encoding="utf-8")

        return output_path

    def _generate_mermaid(self, manifest: ArchitectureManifest) -> str:
        """Mermaidコードを生成"""
        lines = ["graph TB"]
        lines.append("    %% Auto-generated architecture diagram")
        lines.append("")

        # ノードを定義
        for service in manifest.services:
            node_id = self._sanitize_id(service.name)
            icon = self.TYPE_ICONS.get(service.type, "fa:fa-cube")
            label = service.name

            if service.ports:
                label += f"<br/>:{','.join(map(str, service.ports))}"

            # モジュールがある場合はサブグラフとして展開
            if hasattr(service, "modules") and service.modules:
                lines.append(f"    subgraph {node_id} [{icon} {label}]")
                lines.append("        direction TB")
                for module in service.modules:
                    self._generate_module_subgraph(module, lines, indent="        ", parent_path="")
                lines.append("    end")
            else:
                # タイプ別のスタイル
                if service.type == "python":
                    lines.append(f'    {node_id}["{icon} {label}"]:::pythonStyle')
                elif service.type == "docker":
                    lines.append(f'    {node_id}["{icon} {label}"]:::dockerStyle')
                elif service.type == "database":
                    lines.append(f'    {node_id}[("{icon} {label}")]:::dbStyle')
                else:
                    lines.append(f'    {node_id}["{icon} {label}"]')

        lines.append("")

        # 依存関係をエッジとして追加
        for service in manifest.services:
            node_id = self._sanitize_id(service.name)

            # 外部依存関係は表示しない（プロジェクト構造に集中）
            # 依存関係は Services セクションにテキストで記載される

            # 内部依存関係（モジュール間）
            if hasattr(service, "modules") and service.modules:
                # 全てのモジュールIDを収集して、正しい依存関係解決に使用
                all_ids = self._collect_all_module_ids(service.modules)
                self._generate_module_dependencies(
                    service.modules, lines, indent="    ", all_ids=all_ids
                )

        lines.append("")

        # スタイル定義
        lines.append(
            "    classDef pythonStyle fill:#3776ab,stroke:#ffd43b,stroke-width:2px,color:#fff"
        )
        lines.append(
            "    classDef dockerStyle fill:#2496ed,stroke:#1d63ed,stroke-width:2px,color:#fff"
        )
        lines.append("    classDef dbStyle fill:#336791,stroke:#6b9cd6,stroke-width:2px,color:#fff")
        lines.append("    classDef moduleStyle fill:#f9f9f9,stroke:#333,stroke-width:2px")

        # トップレベルモジュール（docgen）にスタイルを適用
        for service in manifest.services:
            if hasattr(service, "modules") and service.modules:
                for module in service.modules:
                    self._sanitize_id(module.name)
        # この部分は_generate_module_subgraph内で処理されるため不要になる
        # for service in manifest.services:
        #     if hasattr(service, "modules") and service.modules:
        #         for module in service.modules:
        #             module_id = self._sanitize_id(module.name)
        #             lines.append(f"    class {module_id} moduleStyle")

        return "\n".join(lines)

    def _generate_module_subgraph(
        self, module: Any, lines: list[str], indent: str, parent_path: str = ""
    ) -> None:
        """モジュールのサブグラフを再帰的に生成"""
        # 完全修飾名を生成（親パスと結合）
        full_path = f"{parent_path}_{module.name}" if parent_path else module.name
        module_id = self._sanitize_id(full_path)

        if module.submodules:
            # サブモジュールがある場合はサブグラフとして描画
            lines.append(f"{indent}subgraph {module_id} [{module.name}]")
            lines.append(f"{indent}    direction TB")

            for submodule in module.submodules:
                self._generate_module_subgraph(submodule, lines, indent + "    ", full_path)

            lines.append(f"{indent}end")

            # サブグラフにスタイルを適用
            lines.append(f"{indent}class {module_id} moduleStyle")
        else:
            # サブモジュールがない場合はノードとして描画
            lines.append(f'{indent}{module_id}["{module.name}"]:::moduleStyle')

    def _collect_all_module_ids(self, modules: list[Any], parent_path: str = "") -> set[str]:
        """全てのモジュールの完全修飾IDを収集"""
        ids = set()
        for module in modules:
            full_path = f"{parent_path}_{module.name}" if parent_path else module.name
            module_id = self._sanitize_id(full_path)
            ids.add(module_id)
            if module.submodules:
                ids.update(self._collect_all_module_ids(module.submodules, full_path))
        return ids

    def _generate_module_dependencies(
        self,
        modules: list[Any],
        lines: list[str],
        indent: str,
        parent_path: str = "",
        all_ids: set[str] | None = None,
    ) -> None:
        """モジュール間の依存関係を生成"""
        if all_ids is None:
            all_ids = set()

        for module in modules:
            # 完全修飾名を生成
            full_path = f"{parent_path}_{module.name}" if parent_path else module.name
            module_id = self._sanitize_id(full_path)

            # このモジュールの依存関係を描画
            for dep in module.dependencies:
                dep_sanitized = self._sanitize_id(dep)

                # 依存先IDの解決を試みる
                # パターン1: 現在のコンテキストでの相対パス (docgen_utils_models)
                candidate1 = f"{parent_path}_{dep_sanitized}" if parent_path else dep_sanitized

                # パターン2: docgen直下のパッケージ (docgen_models)
                # 親パスのルート(docgen)を取得して結合
                root_part = parent_path.split("_")[0] if parent_path else ""
                candidate2 = f"{root_part}_{dep_sanitized}" if root_part else dep_sanitized

                dep_id = candidate1
                if candidate1 not in all_ids and candidate2 in all_ids:
                    dep_id = candidate2
                elif (
                    candidate1 not in all_ids and dep_sanitized in all_ids
                ):  # サービス直下のモジュールへの依存
                    dep_id = dep_sanitized
                elif (
                    candidate1 not in all_ids
                    and candidate2 not in all_ids
                    and dep_sanitized not in all_ids
                ):
                    # どの候補にも見つからない場合は、元のサニタイズされた名前をそのまま使用（外部依存の可能性）
                    dep_id = dep_sanitized

                # 親パッケージへの依存は描画しない
                if parent_path and dep_id == parent_path:
                    continue

                lines.append(f"{indent}{module_id} --> {dep_id}")

            # サブモジュールの依存関係を再帰的に処理
            if module.submodules:
                self._generate_module_dependencies(
                    module.submodules, lines, indent, full_path, all_ids
                )

    def _sanitize_id(self, name: str) -> str:
        """Mermaid IDとして使える形式に変換"""
        # 数字で始まる場合はプレフィックスを付ける
        sanitized = name.replace("-", "_").replace(".", "_").replace(" ", "_")
        if sanitized[0].isdigit():
            return f"_{sanitized}"
        return sanitized

    def _generate_service_list(self, manifest: ArchitectureManifest) -> str:
        """サービスリストを生成（重複を除去）"""
        lines = []
        # サービス名とタイプの組み合わせで重複をチェック
        seen_services: dict[tuple[str, str], Any] = {}

        for service in manifest.services:
            key = (service.name, service.type)
            # 既に同じ名前とタイプのサービスがある場合は、より詳細な情報を持つ方を優先
            if key in seen_services:
                existing = seen_services[key]
                # 既存のサービスにより詳細な情報がある場合はスキップ
                # 依存関係やモジュールがある方を優先
                if existing.dependencies or (hasattr(existing, "modules") and existing.modules):
                    continue
                # 新しいサービスの方が詳細な場合は置き換え
                if service.dependencies or (hasattr(service, "modules") and service.modules):
                    seen_services[key] = service
                    continue
                # どちらも同じ詳細度の場合は最初のものを保持
                continue

            seen_services[key] = service

        # 重複除去後のサービスを出力
        for service in seen_services.values():
            lines.append(f"### {service.name}")
            lines.append(f"- **Type**: {service.type}")
            if service.description:
                lines.append(f"- **Description**: {service.description}")
            if service.ports:
                lines.append(f"- **Ports**: {', '.join(map(str, service.ports))}")
            if service.dependencies:
                lines.append(f"- **Dependencies**: {', '.join(service.dependencies)}")
            lines.append("")
        return "\n".join(lines)
