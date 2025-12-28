"""
パーサーのベースクラス

Template Methodパターンを使用して、コード解析の共通フローを定義します。
サブクラスでは `_parse_to_ast` と `_extract_elements` を実装します。
"""

from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from ...models import APIInfo
from ...utils.exceptions import ParseError
from ...utils.logger import get_logger

if TYPE_CHECKING:
    from ...utils.cache import CacheManager
    from ...utils.gitignore_parser import GitIgnoreMatcher

logger = get_logger("parser")


class BaseParser(ABC):
    """コード解析のベースクラス

    Template Methodパターンにより、解析フローの共通部分を定義します。
    サブクラスでは以下の抽象メソッドを実装します：
    - `_parse_to_ast`: コンテンツをASTにパース
    - `_extract_elements`: ASTからAPI要素を抽出
    - `get_supported_extensions`: サポートする拡張子を返す

    Attributes:
        PARSER_TYPE: パーサーの種類を示すクラス変数
    """

    PARSER_TYPE: ClassVar[str] = "generic"

    def __init__(self, project_root: Path):
        """
        初期化

        Args:
            project_root: プロジェクトのルートディレクトリ
        """
        self.project_root: Path = project_root

    def parse_file(self, file_path: Path) -> list[APIInfo]:
        """
        ファイルを解析してAPI情報を抽出 (Template Method)

        Args:
            file_path: 解析するファイルのパス

        Returns:
            API情報のリスト
        """
        try:
            content = self._read_file(file_path)
            ast = self._parse_to_ast(content, file_path)
            elements = self._extract_elements(ast, file_path)
            return self._post_process(elements)
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(
                message=f"{file_path} の解析に失敗しました",
                file_path=str(file_path),
                language=self.PARSER_TYPE,
                details=str(e),
            ) from e

    def _read_file(self, file_path: Path) -> str:
        """ファイルを読み込む"""
        with open(file_path, encoding="utf-8") as f:
            return f.read()

    @abstractmethod
    def _parse_to_ast(self, content: str, file_path: Path) -> Any:
        """ASTにパース（サブクラスで実装）"""
        pass

    @abstractmethod
    def _extract_elements(self, ast: Any, file_path: Path) -> list[APIInfo]:
        """要素を抽出（サブクラスで実装）"""
        pass

    def _post_process(self, elements: list[APIInfo]) -> list[APIInfo]:
        """後処理（オプション）"""
        return elements

    @abstractmethod
    def get_supported_extensions(self) -> list[str]:
        """
        サポートするファイル拡張子を返す

        Returns:
            拡張子のリスト（例: ['.py', '.pyw']）
        """
        pass

    def get_parser_type(self) -> str:
        """
        パーサーの種類を返す（キャッシュキーの生成に使用）

        Returns:
            パーサーの種類（例: 'python', 'javascript'）
        """
        return self.PARSER_TYPE

    def parse_project(
        self,
        exclude_dirs: list[str] | None = None,
        use_parallel: bool = True,
        max_workers: int | None = None,
        use_cache: bool = True,
        cache_manager: "CacheManager | None" = None,
        files_to_parse: list[tuple[Path, Path]] | None = None,
        skip_cache_save: bool = False,
        gitignore_matcher: "GitIgnoreMatcher | None" = None,
    ) -> list[APIInfo]:
        """
        プロジェクト全体を解析

        Args:
            exclude_dirs: 除外するディレクトリ（例: ['.git', 'node_modules']）
            use_parallel: 並列処理を使用するかどうか（デフォルト: True）
            max_workers: 並列処理の最大ワーカー数（Noneの場合は自動）
            use_cache: キャッシュを使用するかどうか（デフォルト: True）
            cache_manager: キャッシュマネージャー（Noneの場合はキャッシュを使用しない）
            files_to_parse: 既にスキャン済みのファイルリスト（Noneの場合は新規スキャン）
            skip_cache_save: キャッシュ保存をスキップするか（デフォルト: False）
            gitignore_matcher: .gitignoreマッチャー（Noneの場合は.gitignoreを適用しない）

        Returns:
            全API情報のリスト
        """
        if exclude_dirs is None:
            from ...detectors.detector_patterns import DetectorPatterns

            exclude_dirs = list(DetectorPatterns.EXCLUDE_DIRS) + ["docgen", "venv"]

        # キャッシュの設定
        effective_use_cache = use_cache and cache_manager is not None
        parser_type = self.get_parser_type()

        all_apis = []
        extensions = self.get_supported_extensions()
        # 拡張子をセットに変換して高速な検索を可能にする
        extensions_set = {ext.lower() for ext in extensions}

        # プロジェクトルートを正規化（絶対パスに変換）
        project_root_resolved = self.project_root.resolve()

        # 解析対象ファイルのリストを収集（os.walkで一度だけ走査）
        # files_to_parseが提供されている場合はそれを使用（重複スキャンを避ける）
        if files_to_parse is None:
            files_to_parse = []
            try:
                for root, dirs, files in os.walk(self.project_root, followlinks=False):
                    root_path = Path(root)

                    # 除外ディレクトリを早期にスキップ（dirsをin-placeで変更）
                    dirs_to_remove = []
                    for d in dirs:
                        dir_path = root_path / d
                        # 既存の除外チェック
                        if d in exclude_dirs or d.startswith(".") or d.endswith(".egg-info"):
                            dirs_to_remove.append(d)
                            continue
                        # .gitignoreチェック
                        if gitignore_matcher and gitignore_matcher.should_exclude_dir(dir_path):
                            dirs_to_remove.append(d)
                            continue

                    for d in dirs_to_remove:
                        dirs.remove(d)

                    # パスベースの除外チェック（セット検索でO(1)）
                    try:
                        rel_path = root_path.relative_to(project_root_resolved)
                        # セットのintersectionを使用して高速チェック
                        exclude_dirs_set = set(exclude_dirs)
                        if exclude_dirs_set.intersection(rel_path.parts):
                            dirs[:] = []  # このディレクトリ以下をスキップ
                            continue
                        if any(part.endswith(".egg-info") for part in rel_path.parts):
                            dirs[:] = []  # egg-infoディレクトリ以下をスキップ
                            continue
                        # .gitignoreチェック（ディレクトリ全体）
                        if gitignore_matcher and gitignore_matcher.should_exclude_dir(root_path):
                            dirs[:] = []  # このディレクトリ以下をスキップ
                            continue
                    except ValueError:
                        # プロジェクトルート外の場合はスキップ
                        continue

                    # ファイルをチェック
                    for file_name in files:
                        file_path = root_path / file_name

                        # .gitignoreチェック
                        if gitignore_matcher and gitignore_matcher.is_ignored(file_path):
                            continue

                        # 拡張子をチェック
                        ext = file_path.suffix.lower()
                        if ext not in extensions_set:
                            continue

                        try:
                            # パスの正規化（シンボリックリンクを解決）
                            file_path_resolved = file_path.resolve()

                            # プロジェクトルート外へのアクセスを防止
                            try:
                                file_path_relative = file_path_resolved.relative_to(
                                    project_root_resolved
                                )
                            except ValueError:
                                # プロジェクトルート外のファイルはスキップ
                                logger.debug(
                                    f"プロジェクトルート外のファイルをスキップ: {file_path}"
                                )
                                continue

                            # シンボリックリンクのチェック（オプション: シンボリックリンクをスキップする場合）
                            if file_path.is_symlink():
                                logger.debug(f"シンボリックリンクをスキップ: {file_path}")
                                continue

                            files_to_parse.append((file_path, file_path_relative))
                        except (OSError, PermissionError) as e:
                            # ファイルアクセスエラー（権限エラーなど）は無視して続行
                            logger.debug(f"{file_path} へのアクセスに失敗しました: {e}")
                            continue
            except (OSError, PermissionError) as e:
                logger.warning(f"プロジェクトの走査中にエラーが発生しました: {e}")
        else:
            # 提供されたファイルリストから、このパーサーがサポートする拡張子のファイルのみをフィルタリング
            files_to_parse = [
                (file_path, file_path_relative)
                for file_path, file_path_relative in files_to_parse
                if file_path.suffix.lower() in extensions_set
            ]

        # 並列処理または逐次処理で解析
        # 閾値: ファイル数が5を超える場合、またはCPU数が2以上でファイル数が3を超える場合
        import os as os_module

        cpu_count = os_module.cpu_count() or 1
        parallel_threshold = 3 if cpu_count >= 2 else 5
        if use_parallel and len(files_to_parse) > parallel_threshold:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {
                    executor.submit(
                        self._parse_file_safe,
                        file_path,
                        file_path_relative,
                        cache_manager if effective_use_cache else None,
                        parser_type if effective_use_cache else None,
                    ): (file_path, file_path_relative)
                    for file_path, file_path_relative in files_to_parse
                }

                # エラー統計情報
                error_count = 0
                success_count = 0
                parser_type = self.get_parser_type()

                for future in as_completed(future_to_file):
                    file_path, file_path_relative = future_to_file[future]
                    try:
                        apis = future.result()
                        if apis:
                            all_apis.extend(apis)
                            success_count += 1
                        else:
                            # 空の結果（警告のみ、エラーではない）
                            logger.debug(
                                f"[{parser_type}] {file_path_relative}: API要素が見つかりませんでした"
                            )
                            success_count += 1
                    except Exception as e:
                        error_count += 1
                        logger.warning(
                            f"[{parser_type}] {file_path_relative} の解析に失敗しました: {e}",
                            exc_info=logger.isEnabledFor(10),  # DEBUGレベルでスタックトレースを表示
                        )

                # 統計情報をログ出力
                if error_count > 0 or success_count > 0:
                    logger.info(
                        f"[{parser_type}] 解析完了: 成功 {success_count}件, 失敗 {error_count}件"
                    )
        else:
            # 逐次処理
            error_count = 0
            success_count = 0

            for file_path, file_path_relative in files_to_parse:
                try:
                    apis = self._parse_file_safe(
                        file_path,
                        file_path_relative,
                        cache_manager if effective_use_cache else None,
                        parser_type if effective_use_cache else None,
                    )
                    if apis:
                        all_apis.extend(apis)
                        success_count += 1
                    else:
                        # 空の結果（警告のみ、エラーではない）
                        logger.debug(
                            f"[{parser_type}] {file_path_relative}: API要素が見つかりませんでした"
                        )
                        success_count += 1
                except Exception as e:
                    error_count += 1
                    logger.warning(
                        f"[{parser_type}] {file_path_relative} の解析に失敗しました: {e}",
                        exc_info=logger.isEnabledFor(10),  # DEBUGレベルでスタックトレースを表示
                    )
                    continue

            # 統計情報をログ出力
            if error_count > 0 or success_count > 0:
                logger.info(
                    f"[{parser_type}] 解析完了: 成功 {success_count}件, 失敗 {error_count}件"
                )

        # キャッシュを保存（skip_cache_saveがFalseの場合のみ）
        if effective_use_cache and cache_manager and not skip_cache_save:
            cache_manager.save()

        return all_apis

    def _parse_file_safe(
        self,
        file_path: Path,
        file_path_relative: Path,
        cache_manager: "CacheManager | None" = None,
        parser_type: str | None = None,
    ) -> list[APIInfo]:
        """
        ファイルを安全に解析（内部メソッド）

        Args:
            file_path: ファイルパス
            file_path_relative: 相対パス
            cache_manager: キャッシュマネージャー（オプション）
            parser_type: パーサーの種類（オプション）

        Returns:
            API情報のリスト
        """
        # キャッシュから結果を取得
        if cache_manager is not None and parser_type is not None:
            cached_result = cache_manager.get_cached_result(file_path, parser_type)
            if cached_result is not None:
                # キャッシュされた結果をAPIInfoオブジェクトに変換
                result: list[APIInfo] = []
                parser_type_str = parser_type or self.get_parser_type()
                for api_data in cached_result:
                    # キャッシュから取得したデータが辞書の場合はAPIInfoに変換
                    if isinstance(api_data, dict):
                        # 辞書からAPIInfoを作成
                        api_dict = dict(api_data)
                        api_dict["file_path"] = str(file_path_relative)
                        # languageフィールドが不足している場合は追加
                        if "language" not in api_dict:
                            api_dict["language"] = parser_type_str
                        api_info = APIInfo(**api_dict)
                    elif isinstance(api_data, APIInfo):
                        # APIInfoオブジェクトのコピーを作成
                        api_info = APIInfo.model_validate(api_data.model_dump())
                        api_info.file_path = str(file_path_relative)
                    else:
                        continue
                    result.append(api_info)
                return result

        try:
            apis = self.parse_file(file_path)
            # APIInfoオブジェクトのリストを処理
            processed_apis: list[APIInfo] = []
            for api in apis:
                if isinstance(api, dict):
                    # 辞書の場合はAPIInfoに変換（必須フィールドを確認）
                    api_dict = dict(api)
                    api_dict["file_path"] = str(file_path_relative)
                    # languageフィールドが不足している場合は追加
                    if "language" not in api_dict:
                        api_dict["language"] = parser_type or self.get_parser_type()
                    processed_apis.append(APIInfo(**api_dict))
                else:
                    # APIInfoオブジェクトの場合は属性を設定
                    api.file_path = str(file_path_relative)
                    processed_apis.append(api)
            apis = processed_apis

            # 結果をキャッシュに保存
            if cache_manager is not None and parser_type is not None:
                cache_manager.set_cached_result(file_path, parser_type, apis)

            return apis
        except Exception as e:
            parser_type = parser_type or self.get_parser_type()
            logger.warning(
                f"[{parser_type}] {file_path} の解析に失敗しました: {type(e).__name__}: {e}",
                exc_info=logger.isEnabledFor(10),  # DEBUGレベルでスタックトレースを表示
            )
            return []
