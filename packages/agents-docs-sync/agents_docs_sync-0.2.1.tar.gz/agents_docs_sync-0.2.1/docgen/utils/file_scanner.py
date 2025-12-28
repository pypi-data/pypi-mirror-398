"""統一ファイルスキャナーモジュール

プロジェクト全体を一度だけ走査して、必要な情報を収集します。
複数のモジュールで同じプロジェクトルートを走査することを防ぎます。
"""

import os
from pathlib import Path
from typing import Any

from .gitignore_parser import GitIgnoreMatcher
from .logger import get_logger

logger = get_logger(__name__)


class UnifiedFileScanner:
    """プロジェクト全体を一度だけ走査して、必要な情報を収集するクラス"""

    def __init__(
        self,
        project_root: Path,
        exclude_dirs: set[str] | None = None,
        exclude_files: set[str] | None = None,
        gitignore_matcher: GitIgnoreMatcher | None = None,
    ):
        """
        初期化

        Args:
            project_root: プロジェクトルートディレクトリ
            exclude_dirs: 除外するディレクトリ名のセット
            exclude_files: 除外するファイル名のセット
            gitignore_matcher: .gitignoreマッチャー（Noneの場合は.gitignoreを読み込まない）
        """
        self.project_root = Path(project_root).resolve()
        self.exclude_dirs = exclude_dirs or set()
        self.exclude_files = exclude_files or set()
        self.gitignore_matcher = gitignore_matcher
        self._scanned = False
        self._files_by_extension: dict[str, list[Path]] = {}
        self._all_files: list[Path] = []
        self._files_by_relative_path: dict[Path, Path] = {}  # 相対パス -> 絶対パス

    def scan_once(self) -> dict[str, Any]:
        """
        一度だけ走査して結果をキャッシュ

        Returns:
            走査結果の辞書:
            - 'files_by_extension': 拡張子ごとのファイルリスト
            - 'all_files': すべてのファイルのリスト
            - 'files_by_relative_path': 相対パス -> 絶対パスのマッピング
        """
        if self._scanned:
            return {
                "files_by_extension": self._files_by_extension,
                "all_files": self._all_files,
                "files_by_relative_path": self._files_by_relative_path,
            }

        logger.debug(f"Scanning project: {self.project_root}")

        try:
            for root, dirs, files in os.walk(self.project_root, followlinks=False):
                root_path = Path(root)

                # 除外ディレクトリを早期にスキップ（dirsをin-placeで変更）
                dirs_to_remove = []
                for d in dirs:
                    dir_path = root_path / d
                    # 既存の除外チェック
                    if d in self.exclude_dirs or d.startswith(".") or d.endswith(".egg-info"):
                        dirs_to_remove.append(d)
                        continue
                    # .gitignoreチェック
                    if self.gitignore_matcher and self.gitignore_matcher.should_exclude_dir(
                        dir_path
                    ):
                        dirs_to_remove.append(d)
                        continue

                for d in dirs_to_remove:
                    dirs.remove(d)

                # パスベースの除外チェック
                try:
                    rel_path = root_path.relative_to(self.project_root)
                    if any(excluded in rel_path.parts for excluded in self.exclude_dirs):
                        dirs[:] = []  # このディレクトリ以下をスキップ
                        continue
                    if any(part.endswith(".egg-info") for part in rel_path.parts):
                        dirs[:] = []  # egg-infoディレクトリ以下をスキップ
                        continue
                    # .gitignoreチェック（ディレクトリ全体）
                    if self.gitignore_matcher and self.gitignore_matcher.should_exclude_dir(
                        root_path
                    ):
                        dirs[:] = []  # このディレクトリ以下をスキップ
                        continue
                except ValueError:
                    # プロジェクトルート外の場合はスキップ
                    continue

                # ファイルをチェック
                for file_name in files:
                    # 除外ファイル名のチェック
                    if file_name in self.exclude_files:
                        continue

                    file_path = root_path / file_name

                    try:
                        # パスの正規化（シンボリックリンクを解決）
                        file_path_resolved = file_path.resolve()

                        # プロジェクトルート外へのアクセスを防止
                        try:
                            file_path_relative = file_path_resolved.relative_to(self.project_root)
                        except ValueError:
                            # プロジェクトルート外のファイルはスキップ
                            continue

                        # .gitignoreチェック
                        if self.gitignore_matcher and self.gitignore_matcher.is_ignored(
                            file_path_resolved
                        ):
                            continue

                        # シンボリックリンクのチェック（オプション: シンボリックリンクをスキップする場合）
                        if file_path.is_symlink():
                            continue

                        # 拡張子で分類
                        ext = file_path.suffix.lower()
                        if ext not in self._files_by_extension:
                            self._files_by_extension[ext] = []
                        self._files_by_extension[ext].append(file_path_resolved)
                        self._all_files.append(file_path_resolved)
                        self._files_by_relative_path[file_path_relative] = file_path_resolved

                    except (OSError, PermissionError) as e:
                        # ファイルアクセスエラー（権限エラーなど）は無視して続行
                        logger.debug(f"{file_path} へのアクセスに失敗しました: {e}")
                        continue

        except (OSError, PermissionError) as e:
            logger.warning(f"プロジェクトの走査中にエラーが発生しました: {e}")

        self._scanned = True

        logger.debug(
            f"Scanned {len(self._all_files)} files, {len(self._files_by_extension)} extensions"
        )

        return {
            "files_by_extension": self._files_by_extension,
            "all_files": self._all_files,
            "files_by_relative_path": self._files_by_relative_path,
        }

    def get_files_by_extensions(self, extensions: set[str] | list[str]) -> list[tuple[Path, Path]]:
        """
        指定された拡張子のファイルを取得

        Args:
            extensions: 拡張子のセットまたはリスト（例: {'.py', '.js'}）

        Returns:
            (絶対パス, 相対パス) のタプルのリスト
        """
        if not self._scanned:
            self.scan_once()

        extensions_set = {
            ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in extensions
        }
        result = []

        for ext in extensions_set:
            if ext in self._files_by_extension:
                for file_path in self._files_by_extension[ext]:
                    try:
                        rel_path = file_path.relative_to(self.project_root)
                        result.append((file_path, rel_path))
                    except ValueError:
                        continue

        return result

    def get_all_files(self) -> list[tuple[Path, Path]]:
        """
        すべてのファイルを取得

        Returns:
            (絶対パス, 相対パス) のタプルのリスト
        """
        if not self._scanned:
            self.scan_once()

        result = []
        for file_path in self._all_files:
            try:
                rel_path = file_path.relative_to(self.project_root)
                result.append((file_path, rel_path))
            except ValueError:
                continue

        return result

    def clear_cache(self):
        """キャッシュをクリア（再スキャンが必要な場合）"""
        self._scanned = False
        self._files_by_extension.clear()
        self._all_files.clear()
        self._files_by_relative_path.clear()


# グローバルスキャナーインスタンス（プロジェクトルートごと）
_scanner_cache: dict[Path, UnifiedFileScanner] = {}


def get_unified_scanner(
    project_root: Path,
    exclude_dirs: set[str] | None = None,
    exclude_files: set[str] | None = None,
    use_gitignore: bool = True,
) -> UnifiedFileScanner:
    """
    統一ファイルスキャナーのインスタンスを取得（シングルトン的な動作）

    Args:
        project_root: プロジェクトルートディレクトリ
        exclude_dirs: 除外するディレクトリ名のセット
        exclude_files: 除外するファイル名のセット
        use_gitignore: .gitignoreを適用するかどうか

    Returns:
        UnifiedFileScannerインスタンス
    """
    project_root_resolved = Path(project_root).resolve()

    # .gitignoreマッチャーを作成
    gitignore_matcher = None
    if use_gitignore:
        from .gitignore_parser import load_gitignore_patterns

        gitignore_matcher = load_gitignore_patterns(project_root_resolved)

    # 既存のスキャナーがある場合は再利用
    if project_root_resolved in _scanner_cache:
        scanner = _scanner_cache[project_root_resolved]
        # 除外設定が変更された場合は新しいスキャナーを作成
        if (
            scanner.exclude_dirs == (exclude_dirs or set())
            and scanner.exclude_files == (exclude_files or set())
            and scanner.gitignore_matcher == gitignore_matcher
        ):
            return scanner

    # 新しいスキャナーを作成
    from ..detectors.detector_patterns import DetectorPatterns

    default_exclude_dirs = set(DetectorPatterns.EXCLUDE_DIRS)
    if exclude_dirs:
        default_exclude_dirs.update(exclude_dirs)

    scanner = UnifiedFileScanner(
        project_root=project_root_resolved,
        exclude_dirs=default_exclude_dirs,
        exclude_files=exclude_files or set(),
        gitignore_matcher=gitignore_matcher,
    )
    _scanner_cache[project_root_resolved] = scanner

    return scanner
