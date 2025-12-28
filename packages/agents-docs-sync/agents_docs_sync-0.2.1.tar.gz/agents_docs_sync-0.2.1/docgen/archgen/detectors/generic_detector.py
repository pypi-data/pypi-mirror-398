"""
汎用プロジェクト検出器
"""

from pathlib import Path

from docgen.detectors.detector_patterns import DetectorPatterns
from docgen.utils.file_utils import safe_read_json

from ..models import Module, Service


class GenericDetector:
    """様々なプログラミング言語のプロジェクトを検出"""

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
        self.exclude_dirs = set(exclude_directories) if exclude_directories else set()
        # DetectorPatternsからデフォルトの除外ディレクトリも取得
        self.exclude_dirs.update(DetectorPatterns.EXCLUDE_DIRS)
        self.exclude_patterns = exclude_patterns or set()

    def detect(self, project_root: Path) -> list[Service]:
        """プロジェクトをスキャンしてサービスを検出"""
        services = []

        # JavaScript/TypeScriptプロジェクトの詳細解析
        js_service = self._detect_javascript_typescript(project_root)
        if js_service:
            services.append(js_service)

        # その他の言語の検出
        for lang, files in DetectorPatterns.PACKAGE_FILES.items():
            # PythonとJavaScript/TypeScriptは既に処理済み
            if lang in ("python", "javascript", "typescript"):
                continue

            for file_pattern in files:
                # glob形式をサポート（*.csproj など）
                found = False
                if "*" in file_pattern:
                    if list(project_root.glob(file_pattern)):
                        found = True
                elif (project_root / file_pattern).exists():
                    found = True

                if found:
                    services.append(
                        Service(
                            name=project_root.name,
                            type=lang,
                            description=f"{lang.capitalize()} project detected by {file_pattern}",
                            metadata={"entry_file": file_pattern},
                            dependencies=[],
                        )
                    )
                    # 1つの言語に対して1つのファイルが見つかれば十分
                    break

        # パッケージマネージャーファイルが見つからない場合、ソースファイルの存在を確認
        if not services:
            for lang, _exts in DetectorPatterns.SOURCE_EXTENSIONS.items():
                if lang in ("python", "javascript", "typescript"):
                    continue

                # パフォーマンスのため、トップレベルまたは1段階下のディレクトリのみをチェック（archgenの用途的に）
                # 全走査は重いので DetectorPatterns.detect_by_source_files_with_exclusions を使う
                if DetectorPatterns.detect_by_source_files_with_exclusions(project_root, lang):
                    services.append(
                        Service(
                            name=project_root.name,
                            type=lang,
                            description=f"{lang.capitalize()} project detected by source files",
                            metadata={},
                            dependencies=[],
                        )
                    )

        return services

    def _detect_javascript_typescript(self, project_root: Path) -> Service | None:
        """JavaScript/TypeScriptプロジェクトを検出して詳細情報を抽出"""
        package_json = project_root / "package.json"
        if not package_json.exists():
            return None

        package_data = safe_read_json(package_json)
        if not package_data:
            return None

        # 依存関係を抽出
        dependencies = []
        if "dependencies" in package_data:
            dependencies.extend(package_data["dependencies"].keys())
        if "devDependencies" in package_data:
            dependencies.extend(package_data["devDependencies"].keys())

        # TypeScriptかどうかを判定
        is_typescript = False
        if "devDependencies" in package_data:
            is_typescript = any(
                dep in package_data["devDependencies"]
                for dep in ["typescript", "@types/node", "ts-node"]
            )
        if not is_typescript and "dependencies" in package_data:
            is_typescript = "typescript" in package_data["dependencies"]

        # tsconfig.jsonの存在も確認
        if not is_typescript:
            is_typescript = (project_root / "tsconfig.json").exists()

        lang_type = "typescript" if is_typescript else "javascript"

        # モジュール構造をスキャン
        modules = self._scan_js_modules(project_root, lang_type)

        # 依存関係をフィルタリング
        filtered_dependencies = self._filter_dependencies(dependencies)

        # 説明を取得（検証と改善を含む）
        description = package_data.get("description", f"{lang_type.capitalize()} project")
        description = self._validate_and_improve_description(description, package_data)

        return Service(
            name=package_data.get("name", project_root.name),
            type=lang_type,
            description=description,
            metadata={
                "version": package_data.get("version", "0.0.0"),
                "main": package_data.get("main"),
                "entry_file": "package.json",
            },
            dependencies=sorted(set(filtered_dependencies)),
            modules=modules,
        )

    def _scan_js_modules(self, project_root: Path, lang_type: str) -> list[Module]:
        """JavaScript/TypeScriptプロジェクトのモジュール構造をスキャン"""
        modules = []
        extensions = DetectorPatterns.SOURCE_EXTENSIONS.get(lang_type, [])
        if not extensions:
            # フォールバック
            extensions = [".js", ".jsx", ".ts", ".tsx"]

        # プロジェクトルート直下のディレクトリを探索
        for item in project_root.iterdir():
            if (
                item.is_dir()
                and item.name not in self.exclude_dirs
                and not item.name.startswith(".")
            ):
                # srcディレクトリを優先的に探索（深く探索）
                if item.name == "src":
                    module = self._scan_js_directory(item, project_root, extensions, max_depth=4)
                    if module:
                        modules.append(module)
                # その他の一般的なディレクトリも探索
                elif item.name in (
                    "lib",
                    "app",
                    "components",
                    "pages",
                    "modules",
                    "services",
                    "utils",
                    "core",
                ):
                    module = self._scan_js_directory(item, project_root, extensions, max_depth=3)
                    if module:
                        modules.append(module)
                # その他のディレクトリも探索（浅く探索）
                else:
                    # ディレクトリ内にJavaScript/TypeScriptファイルがあるか確認
                    has_js_files = False
                    for ext in extensions:
                        # 直接のファイルと1階層下のファイルをチェック
                        if list(item.glob(f"*{ext}")) or list(item.glob(f"*/*{ext}")):
                            has_js_files = True
                            break

                    if has_js_files:
                        module = self._scan_js_directory(
                            item, project_root, extensions, max_depth=2
                        )
                        if module:
                            modules.append(module)

        return modules

    def _scan_js_directory(
        self,
        path: Path,
        project_root: Path,
        extensions: list[str],
        max_depth: int = 2,
        depth: int = 0,
    ) -> Module | None:
        """JavaScript/TypeScriptディレクトリを再帰的にスキャン"""
        if depth > max_depth:
            return None

        # ディレクトリ内に該当する拡張子のファイルがあるか確認
        # 現在のディレクトリ直下と1階層下をチェック（パフォーマンス向上）
        has_files = False
        for ext in extensions:
            # 直接のファイル
            if list(path.glob(f"*{ext}")):
                has_files = True
                break
            # 1階層下のファイル（再帰的検索は重いので制限）
            if depth < max_depth and list(path.glob(f"*/*{ext}")):
                has_files = True
                break

        if not has_files:
            return None

        submodules = []
        for item in path.iterdir():
            if (
                item.is_dir()
                and item.name not in self.exclude_dirs
                and not item.name.startswith(".")
            ):
                submodule = self._scan_js_directory(
                    item, project_root, extensions, max_depth, depth + 1
                )
                if submodule:
                    submodules.append(submodule)

        # pathはPath型である必要がある
        rel_path = path.relative_to(project_root)
        return Module(
            name=path.name,
            path=rel_path,
            submodules=submodules,
        )

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

    def _validate_and_improve_description(self, description: str, package_data: dict) -> str:
        """
        サービス説明を検証し、必要に応じて改善

        Args:
            description: 現在の説明
            package_data: package.jsonのデータ

        Returns:
            検証・改善後の説明
        """
        # デフォルト説明のパターン
        default_patterns = [
            "Add your description here",
            "Add your description",
            "プロジェクトの説明をここに記述してください",
            "このプロジェクトの説明をここに記述してください",
        ]

        # デフォルト説明が検出された場合、または説明が空の場合
        is_default = (
            not description
            or description.strip() in default_patterns
            or any(pattern in description for pattern in default_patterns)
        )

        if is_default:
            # package.jsonから説明を再取得を試みる
            if "description" in package_data and package_data["description"]:
                desc = package_data["description"].strip()
                if desc and desc not in default_patterns:
                    return desc

            # 説明が見つからない場合は空文字列を返す
            return ""

        return description
