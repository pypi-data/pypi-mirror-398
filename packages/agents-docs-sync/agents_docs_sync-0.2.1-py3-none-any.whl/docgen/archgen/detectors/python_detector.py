"""
Python プロジェクト検出器
"""

from pathlib import Path
import tomllib

from ..models import Module, Service


class PythonDetector:
    """Python プロジェクトを検出"""

    # デフォルトの除外ディレクトリ
    DEFAULT_EXCLUDE_DIRS = {"tests", "docs", "venv", ".git", "__pycache__"}

    def __init__(
        self,
        exclude_directories: list[str] | None = None,
        exclude_patterns: set[str] | None = None,
    ):
        """
        初期化

        Args:
            exclude_directories: 除外するディレクトリのリスト
            exclude_patterns: 依存関係から除外するパターンのセット
        """
        self.exclude_dirs = self.DEFAULT_EXCLUDE_DIRS.copy()
        if exclude_directories:
            self.exclude_dirs.update(exclude_directories)
        self.exclude_patterns = exclude_patterns or set()

    def detect(self, project_root: Path) -> list[Service]:
        services = []

        # pyproject.toml の検出
        pyproject = project_root / "pyproject.toml"
        if pyproject.exists():
            service = self._parse_pyproject(pyproject)
            if service:
                # モジュール構造のスキャン
                service.modules = self._scan_modules(project_root)
                services.append(service)

        # requirements*.txt の検出
        if services:
            for req_file in project_root.glob("requirements*.txt"):
                deps = self._parse_requirements(req_file)
                services[0].dependencies.extend(deps)

        # 重複を除去
        if services:
            services[0].dependencies = sorted(set(services[0].dependencies))
            # 依存関係をフィルタリング
            services[0].dependencies = self._filter_dependencies(services[0].dependencies)

        return services

    def _filter_dependencies(self, dependencies: list[str]) -> list[str]:
        """
        依存関係から除外パターンに一致するものを除去

        Args:
            dependencies: 依存関係のリスト

        Returns:
            フィルタリング後の依存関係のリスト
        """
        if not self.exclude_patterns:
            return dependencies

        filtered = []
        for dep in dependencies:
            # パッケージ名の正規化（ハイフン/アンダースコアを統一）
            dep_normalized = dep.lower().replace("-", "_")
            dep_normalized_alt = dep.lower().replace("_", "-")

            # 除外パターンに一致するかチェック
            should_exclude = False
            for pattern in self.exclude_patterns:
                pattern_normalized = pattern.lower().replace("-", "_")
                pattern_normalized_alt = pattern.lower().replace("_", "-")

                # 完全一致または部分一致をチェック
                if (
                    dep.lower() == pattern.lower()
                    or dep_normalized == pattern_normalized
                    or dep_normalized_alt == pattern_normalized_alt
                    or dep.lower().startswith(pattern.lower() + "-")
                    or dep.lower().startswith(pattern.lower() + "_")
                ):
                    should_exclude = True
                    break

            if not should_exclude:
                filtered.append(dep)

        return filtered

    def _scan_modules(self, project_root: Path) -> list[Module]:
        """プロジェクト内のモジュールをスキャン"""

        modules = []
        # プロジェクトルート直下のディレクトリを探索（パッケージのみ）
        for path in project_root.iterdir():
            if path.is_dir() and (path / "__init__.py").exists():
                # 除外ディレクトリのチェック
                if path.name.startswith(".") or path.name in self.exclude_dirs:
                    continue

                module = self._scan_package(path, project_root)
                if module:
                    modules.append(module)

        return modules

    def _scan_package(
        self, path: Path, project_root: Path, depth: int = 0, max_depth: int = 2
    ) -> Module:
        """パッケージを再帰的にスキャン（最大深度制限付き）"""

        submodules = []
        dependencies = set()

        # 最大深度に達したら、これ以上スキャンしない
        if depth >= max_depth:
            # 浅いパッケージでも依存関係を収集
            deps = self._collect_package_dependencies(path, project_root)
            return Module(
                name=path.name,
                path=path.relative_to(project_root),
                is_package=True,
                submodules=[],
                dependencies=sorted(deps),
            )

        # パッケージ内のサブパッケージのみをスキャン（個別ファイルは無視）
        for item in path.iterdir():
            if item.is_dir() and (item / "__init__.py").exists():
                if item.name == "__pycache__":
                    continue
                submodule = self._scan_package(item, project_root, depth + 1, max_depth)
                submodules.append(submodule)

        # このパッケージ全体の依存関係を収集
        # ただし、トップレベル（depth=0）では収集しない（冗長な矢印を避けるため）
        if depth > 0:
            pkg_deps = self._collect_package_dependencies(path, project_root)
            dependencies.update(pkg_deps)

        return Module(
            name=path.name,
            path=path.relative_to(project_root),
            is_package=True,
            submodules=submodules,
            dependencies=sorted(dependencies),
        )

    def _collect_package_dependencies(self, package_path: Path, project_root: Path) -> set[str]:
        """パッケージ内の全Pythonファイルから内部パッケージへの依存を収集"""
        dependencies = set()

        # 現在のパッケージ名を取得
        current_package_rel = package_path.relative_to(project_root)
        if current_package_rel.parts[0] == "docgen" and len(current_package_rel.parts) > 1:
            current_package = current_package_rel.parts[1]
        else:
            current_package = package_path.name

        # プロジェクトのトップレベルパッケージ（docgen）の直下にあるパッケージ一覧
        # これらが認識すべき内部パッケージ
        docgen_packages = {
            "collectors",
            "utils",
            "models",
            "archgen",
            "detectors",
            "generators",
            "rag",
        }

        # パッケージ内の全.pyファイルをスキャン
        for py_file in package_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            imports = self._parse_imports(py_file)
            for imp in imports:
                # パターン1: 絶対インポート "docgen.models" -> "models"
                if imp.startswith("docgen."):
                    parts = imp.split(".")
                    if len(parts) >= 2 and parts[1] in docgen_packages:
                        target_package = parts[1]
                        if target_package != current_package:
                            dependencies.add(target_package)
                # パターン2: 直接インポート "models" or "utils" (同じプロジェクト内)
                elif imp in docgen_packages and imp != current_package:
                    dependencies.add(imp)

        return dependencies

    def _parse_imports(self, path: Path) -> list[str]:
        """Pythonファイルからインポートを抽出"""
        import ast

        deps = set()
        try:
            with open(path, encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(path))

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        deps.add(name.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        deps.add(node.module.split(".")[0])
        except Exception:
            pass
        return list(deps)

    def _parse_pyproject(self, path: Path) -> Service | None:
        """pyproject.toml をパース"""
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)

            project = data.get("project", {})
            dependencies = []

            # project.dependencies
            if "dependencies" in project:
                deps = self._extract_package_names(project["dependencies"])
                dependencies.extend(deps)

            # dependency-groups (PEP 735 / uv)
            dep_groups = data.get("dependency-groups", {})
            for group_deps in dep_groups.values():
                dependencies.extend(self._extract_package_names(group_deps))

            # tool.poetry.dependencies (Poetry support)
            poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
            if poetry_deps:
                dependencies.extend(poetry_deps.keys())

            # 説明を取得（検証と改善を含む）
            description = project.get("description", "")
            description = self._validate_and_improve_description(description, project, data)

            return Service(
                name=project.get("name", "unknown"),
                type="python",
                description=description,
                metadata={"version": project.get("version", "0.0.0")},
                dependencies=dependencies,
            )
        except Exception:
            return None

    def _validate_and_improve_description(self, description: str, project: dict, data: dict) -> str:
        """
        サービス説明を検証し、必要に応じて改善

        Args:
            description: 現在の説明
            project: projectセクションのデータ
            data: pyproject.toml全体のデータ

        Returns:
            検証・改善後の説明
        """
        # デフォルト説明のパターン
        default_patterns = [
            "Add your description here",
            "Add your description",
            "プロジェクトの説明をここに記述してください",
            "このプロジェクトの説明をここに記述してください",
            "",
        ]

        # デフォルト説明が検出された場合、または説明が空の場合
        is_default = (
            not description
            or description.strip() in default_patterns
            or any(pattern in description for pattern in default_patterns)
        )

        if is_default:
            # pyproject.tomlから説明を再取得を試みる
            # project.description
            if "description" in project and project["description"]:
                desc = project["description"].strip()
                if desc and desc not in default_patterns:
                    return desc

            # tool.poetry.description
            poetry = data.get("tool", {}).get("poetry", {})
            if "description" in poetry and poetry["description"]:
                desc = poetry["description"].strip()
                if desc and desc not in default_patterns:
                    return desc

            # 説明が見つからない場合は空文字列を返す（Noneではなく）
            return ""

        return description

    def _parse_requirements(self, path: Path) -> list[str]:
        """requirements.txt から依存パッケージを抽出"""
        deps = []
        try:
            with open(path) as f:
                lines = f.readlines()
                deps = self._extract_package_names(lines)  # type: ignore[arg-type]
        except Exception:
            pass
        return deps

    def _extract_package_names(self, lines: list[str | dict]) -> list[str]:
        """依存関係リストからパッケージ名を抽出"""
        deps = []
        for line in lines:
            # 辞書形式の場合（include-groupなど）はスキップ
            if isinstance(line, dict):
                continue

            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # バージョン指定などを除去
            # e.g., "package>=1.0.0" -> "package"
            # e.g., "package[extra]>=1.0.0" -> "package"
            pkg = (
                line.split(">=")[0]
                .split("==")[0]
                .split("<")[0]
                .split("~=")[0]
                .split("!=")[0]
                .strip()
            )
            pkg = pkg.split("[")[0].strip()  # extrasを除去

            if pkg and pkg != "python":  # python自体の指定を除外
                deps.append(pkg)
        return deps
