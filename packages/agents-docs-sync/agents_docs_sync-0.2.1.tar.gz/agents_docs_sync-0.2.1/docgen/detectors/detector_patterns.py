"""Common file detection patterns for language detectors."""

import os
from pathlib import Path
from typing import Any


class DetectorPatterns:
    """Common file detection patterns used by language detectors."""

    # ファイル検索結果のキャッシュ（プロジェクトルートごと）
    _file_cache: dict[Path, dict[tuple[str, ...], bool]] = {}

    # 統合ファイル検索結果のキャッシュ（一度の走査で全言語を検出）
    _unified_scan_cache: dict[Path, dict[str, bool]] = {}

    # カスタム除外ディレクトリ（設定ファイルから読み込まれる）
    _custom_exclude_dirs: set[str] = set()

    # Package manager detection patterns: list of (file_patterns, manager_name)
    # file_patterns can be str or tuple of str (all must exist)
    # Order matters - more specific/priority files first
    PACKAGE_MANAGER_PATTERNS = {
        "python": [
            ("uv.lock", "uv"),
            ("poetry.lock", "poetry"),
            # pyproject.toml handled separately due to content check
            ("Pipfile.lock", "pipenv"),
            ("environment.yml", "conda"),
            ("conda-environment.yml", "conda"),
            ("requirements.txt", "pip"),
            ("setup.py", "pip"),
        ],
        "javascript": [
            ("pnpm-lock.yaml", "pnpm"),
            ("yarn.lock", "yarn"),
            ("package-lock.json", "npm"),
            ("bun.lockb", "bun"),
            ("package.json", "npm"),  # fallback
        ],
        "go": [
            ("go.mod", "go"),
            (("Gopkg.toml", "Gopkg.lock"), "dep"),
            (("glide.yaml", "glide.lock"), "glide"),
        ],
    }

    # Package manager files by language
    PACKAGE_FILES = {
        "python": [
            "requirements.txt",
            "setup.py",
            "pyproject.toml",
            "Pipfile",
            "Pipfile.lock",
            "poetry.lock",
            "environment.yml",
            "conda-environment.yml",
            "uv.lock",
        ],
        "javascript": [
            "package.json",
            "yarn.lock",
            "pnpm-lock.yaml",
            "package-lock.json",
            "bun.lockb",
        ],
        "typescript": [
            "tsconfig.json",
            "package.json",  # TypeScript projects usually have package.json too
        ],
        "go": [
            "go.mod",
            "go.sum",
            "glide.yaml",
            "glide.lock",
            "Gopkg.toml",
            "Gopkg.lock",
        ],
        "rust": [
            "Cargo.toml",
            "Cargo.lock",
        ],
        "java": [
            "pom.xml",
            "build.gradle",
            "build.gradle.kts",
        ],
        "csharp": [
            "*.csproj",
            "*.sln",
        ],
        "cpp": [
            "CMakeLists.txt",
            "Makefile",
            "configure.ac",
            "configure.in",
        ],
    }

    # Source file extensions by language
    SOURCE_EXTENSIONS = {
        "python": [".py", ".pyx", ".pyw"],
        "javascript": [".js", ".jsx", ".mjs", ".cjs"],
        "typescript": [".ts", ".tsx", ".d.ts"],
        "go": [".go"],
        "rust": [".rs"],
        "java": [".java"],
        "csharp": [".cs"],
        "cpp": [".cpp", ".cc", ".cxx", ".c++", ".hpp", ".hxx", ".h"],
        "c": [".c", ".h"],
        "ruby": [".rb"],
        "php": [".php"],
        "swift": [".swift"],
        "kotlin": [".kt"],
        "scala": [".scala"],
        "dart": [".dart"],
        "r": [".r", ".R"],
        "lua": [".lua"],
        "perl": [".pl", ".pm"],
        "shell": [".sh", ".bash", ".zsh"],
        "powershell": [".ps1"],
    }

    # Common directories to exclude
    EXCLUDE_DIRS = {
        ".venv",
        ".git",
        "__pycache__",
        "node_modules",
        "htmlcov",
        "coverage",
        ".coverage",
        "site-packages",
        "dist",
        "build",
        ".next",
        ".nuxt",
        "target",  # Rust
        "bin",
        "obj",  # .NET
        ".gradle",
        ".idea",
        ".vscode",
        ".DS_Store",
        ".pytest_cache",
        ".mypy_cache",
        ".tox",
    }

    # Languages supported by GenericDetector
    GENERIC_LANGUAGES = {
        "rust": [".rs"],
        "java": [".java"],
        "kotlin": [".kt", ".kts"],
        "scala": [".scala"],
        "ruby": [".rb"],
        "php": [".php"],
        "c": [".c", ".h"],
        "cpp": [".cpp", ".cc", ".cxx", ".hpp", ".hxx"],
        "csharp": [".cs"],
        "swift": [".swift"],
        "dart": [".dart"],
        "r": [".r", ".R"],
        "lua": [".lua"],
        "perl": [".pl", ".pm"],
        "shell": [".sh", ".bash", ".zsh"],
        "powershell": [".ps1"],
    }

    # JavaScript/TypeScript config and test files to exclude
    EXCLUDE_JS_FILES = {
        "webpack.config",
        "rollup.config",
        "vite.config",
        "babel.config",
        ".eslintrc",
        ".prettierrc",
        "jest.config",
        "vitest.config",
        "tsconfig",
        "jsconfig",
        "package-lock",
        "yarn.lock",
        "pnpm-lock",
        ".test.",
        ".spec.",
        "test.",
        "spec.",
        "coverage",
        "htmlcov",
        ".coverage",
    }

    @classmethod
    def get_package_files(cls, language: str) -> list[str]:
        """Get package manager files for a language."""
        return cls.PACKAGE_FILES.get(language, [])

    @classmethod
    def get_source_extensions(cls, language: str) -> list[str]:
        """Get source file extensions for a language."""
        return cls.SOURCE_EXTENSIONS.get(language, [])

    @classmethod
    def detect_by_package_files(cls, project_root: Path, language: str) -> bool:
        """Detect language by checking for package manager files."""
        package_files = cls.get_package_files(language)
        return any((project_root / file).exists() for file in package_files)

    @classmethod
    def detect_by_source_files(cls, project_root: Path, language: str) -> bool:
        """Detect language by checking for source files."""
        extensions = cls.get_source_extensions(language)
        for ext in extensions:
            try:
                for _ in project_root.rglob(f"*{ext}"):
                    return True
            except (OSError, PermissionError):
                continue
        return False

    @classmethod
    def detect_by_source_files_with_exclusions(cls, project_root: Path, language: str) -> bool:
        """Detect language by checking for source files, excluding common directories."""
        extensions = cls.get_source_extensions(language)
        # キャッシュ機能を使用
        return cls.detect_by_extensions_with_exclusions(project_root, extensions)

    @classmethod
    def _unified_scan_for_all_languages(cls, project_root: Path) -> dict[str, bool]:
        """一度の走査で全言語を検出（os.walkを使用して高速化）

        Args:
            project_root: プロジェクトルートディレクトリ

        Returns:
            言語名をキー、検出結果を値とする辞書
        """
        # キャッシュをチェック
        if project_root in cls._unified_scan_cache:
            return cls._unified_scan_cache[project_root]

        # 全言語の拡張子マップを作成（拡張子 -> 言語のリスト）
        ext_to_languages: dict[str, list[str]] = {}
        for lang, exts in cls.SOURCE_EXTENSIONS.items():
            for ext in exts:
                if ext not in ext_to_languages:
                    ext_to_languages[ext] = []
                ext_to_languages[ext].append(lang)

        # 検出結果を初期化
        detected_languages: dict[str, bool] = dict.fromkeys(cls.SOURCE_EXTENSIONS.keys(), False)

        # os.walkで一度だけ走査（除外ディレクトリを早期にスキップ）
        # カスタム除外ディレクトリも含めた全除外ディレクトリを取得
        all_exclude_dirs = cls.get_all_exclude_dirs()
        try:
            for root, dirs, files in os.walk(project_root, followlinks=False):
                # 除外ディレクトリを早期にスキップ（dirsをin-placeで変更）
                dirs[:] = [d for d in dirs if d not in all_exclude_dirs and not d.startswith(".")]

                # パスベースの除外チェック（セット検索でO(1)）
                root_path = Path(root)
                try:
                    rel_path = root_path.relative_to(project_root)
                    # セットのintersectionを使用して高速チェック
                    if all_exclude_dirs.intersection(rel_path.parts):
                        dirs[:] = []  # このディレクトリ以下をスキップ
                        continue
                except ValueError:
                    # プロジェクトルート外の場合はスキップ
                    continue

                # ファイルをチェック
                for file_name in files:
                    file_path = root_path / file_name

                    # ファイル拡張子をチェック
                    ext = file_path.suffix.lower()
                    if ext in ext_to_languages:
                        # 大きなファイルをスキップ
                        try:
                            if file_path.stat().st_size > 10 * 1024 * 1024:  # 10MB
                                continue
                        except (OSError, PermissionError):
                            continue

                        # 該当する言語を検出済みにマーク
                        for lang in ext_to_languages[ext]:
                            detected_languages[lang] = True
        except (OSError, PermissionError):
            pass

        # キャッシュに保存
        cls._unified_scan_cache[project_root] = detected_languages
        return detected_languages

    @classmethod
    def detect_by_extensions_with_exclusions(
        cls, project_root: Path, extensions: list[str], max_file_size: int = 10 * 1024 * 1024
    ) -> bool:
        """Detect files by extensions, excluding common directories.

        Args:
            project_root: プロジェクトルートディレクトリ
            extensions: 検索する拡張子のリスト
            max_file_size: スキップする最大ファイルサイズ（バイト、デフォルト: 10MB）
                          大きなファイルは検出対象外として扱う
        """
        # キャッシュキー: 拡張子のソート済みタプル
        cache_key = tuple(sorted(extensions))

        # キャッシュをチェック
        if project_root in cls._file_cache:
            if cache_key in cls._file_cache[project_root]:
                return cls._file_cache[project_root][cache_key]
        else:
            cls._file_cache[project_root] = {}

        # 統合スキャンの結果を利用（一度の走査で全言語を検出）
        unified_results = cls._unified_scan_for_all_languages(project_root)

        # 拡張子から言語を逆引き
        ext_to_languages: dict[str, list[str]] = {}
        for lang, exts in cls.SOURCE_EXTENSIONS.items():
            for ext in exts:
                if ext not in ext_to_languages:
                    ext_to_languages[ext] = []
                ext_to_languages[ext].append(lang)

        # 指定された拡張子に対応する言語が検出されているかチェック
        result = False
        for ext in extensions:
            if ext in ext_to_languages:
                for lang in ext_to_languages[ext]:
                    if unified_results.get(lang, False):
                        result = True
                        break
                if result:
                    break

        # キャッシュに保存
        cls._file_cache[project_root][cache_key] = result
        return result

    @classmethod
    def is_excluded_path(cls, path: Path, project_root: Path) -> bool:
        """Check if a path should be excluded from detection."""
        try:
            relative_path = path.relative_to(project_root)
            return any(part in cls.EXCLUDE_DIRS for part in relative_path.parts)
        except ValueError:
            # Path is outside project root
            return True

    @classmethod
    def detect_package_manager(cls, language: str, file_exists_func) -> str | None:
        """Detect package manager for a language using file existence checks.

        Args:
            language: Language name
            file_exists_func: Function that takes file patterns (str or tuple) and returns bool

        Returns:
            Package manager name or None
        """
        patterns = cls.PACKAGE_MANAGER_PATTERNS.get(language, [])
        if not isinstance(patterns, list):
            return None
        for file_patterns, manager in patterns:
            if isinstance(file_patterns, tuple):
                if file_exists_func(*file_patterns):
                    return manager
            else:
                if file_exists_func(file_patterns):
                    return manager
        return None

    @classmethod
    def is_js_config_or_test(cls, file_path: Path) -> bool:
        """Check if a file is likely a JavaScript config or test file."""
        name = file_path.name.lower()
        return any(pattern in name for pattern in cls.EXCLUDE_JS_FILES)

    @classmethod
    def clear_cache(cls, project_root: Path | None = None) -> None:
        """Clear file detection cache.

        Args:
            project_root: If provided, clear cache for this project only.
                         If None, clear all caches.
        """
        if project_root is None:
            cls._file_cache.clear()
            cls._unified_scan_cache.clear()
            cls._custom_exclude_dirs.clear()
        else:
            if project_root in cls._file_cache:
                del cls._file_cache[project_root]
            if project_root in cls._unified_scan_cache:
                del cls._unified_scan_cache[project_root]

    @classmethod
    def set_custom_exclude_dirs(cls, directories: list[str]) -> None:
        """設定ファイルからのカスタム除外ディレクトリを設定.

        Args:
            directories: 除外するディレクトリ名のリスト
        """
        cls._custom_exclude_dirs = set(directories)
        # 除外ディレクトリが変更された場合、キャッシュをクリア
        cls._file_cache.clear()
        cls._unified_scan_cache.clear()

    @classmethod
    def get_all_exclude_dirs(cls) -> set[str]:
        """デフォルトとカスタムの除外ディレクトリをマージして取得.

        Returns:
            除外ディレクトリのセット
        """
        return cls.EXCLUDE_DIRS | cls._custom_exclude_dirs

    @classmethod
    def detect_python_package_manager(cls, project_root: Path) -> str | None:
        """Detect Python package manager with special handling for pyproject.toml."""
        # uv.lockが存在する場合（優先度最高）
        if (project_root / "uv.lock").exists():
            return "uv"

        # poetry.lockが存在する場合
        if (project_root / "poetry.lock").exists():
            return "poetry"

        # pyproject.tomlが存在し、[tool.poetry]セクションがある場合
        pyproject_path = project_root / "pyproject.toml"
        if pyproject_path.exists():
            # 先頭8KBだけ読んで高速に判定（[tool.poetry]セクションは通常ファイルの先頭付近にある）
            # 大きなファイルでも高速に処理できる
            MAX_READ_SIZE = 8 * 1024  # 8KB
            try:
                with open(pyproject_path, "rb") as f:
                    # 先頭部分だけ読み込む
                    content = f.read(MAX_READ_SIZE)
                    # 文字列検索で高速に判定（バイト列で検索）
                    # [tool.poetry]が見つかった場合のみ、ファイル全体を読み込んで正確に判定
                    if b"[tool.poetry]" in content or b"[tool.poetry]" in content:
                        try:
                            import tomllib

                            f.seek(0)
                            data = tomllib.load(f)
                            if "tool" in data and "poetry" in data["tool"]:
                                return "poetry"
                        except ImportError:
                            # tomllibが利用できない場合（Python 3.10以前）
                            # 先頭部分に[tool.poetry]があればpoetryと判定
                            return "poetry"
                        except Exception:
                            # パースエラーでも、先頭部分に[tool.poetry]があればpoetryと判定
                            return "poetry"
            except Exception:
                pass

        # environment.ymlまたはconda-environment.ymlが存在する場合
        if (project_root / "environment.yml").exists() or (
            project_root / "conda-environment.yml"
        ).exists():
            return "conda"

        # requirements.txtが存在する場合（デフォルト）
        if (project_root / "requirements.txt").exists():
            return "pip"

        # setup.pyが存在する場合
        if (project_root / "setup.py").exists():
            return "pip"

        return None
