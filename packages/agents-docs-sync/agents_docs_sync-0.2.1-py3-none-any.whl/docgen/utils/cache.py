"""
キャッシュ管理モジュール
ファイル解析結果をキャッシュして、パフォーマンスを向上させます
"""

from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import Any

from ..models.api import APIInfo
from ..models.cache import CacheEntry, CacheMetadata
from .exceptions import ErrorMessages
from .logger import get_logger

logger = get_logger("cache")


class CacheManager:
    """キャッシュ管理クラス"""

    def __init__(self, project_root: Path, cache_dir: Path | None = None, enabled: bool = True):
        """
        初期化

        Args:
            project_root: プロジェクトのルートディレクトリ
            cache_dir: キャッシュディレクトリ（Noneの場合は`docgen/.cache/`）
            enabled: キャッシュを有効にするかどうか
        """
        self.project_root: Path = project_root.resolve()
        self.enabled: bool = enabled
        self.cache_dir: Path = cache_dir or (project_root / "docgen" / ".cache")
        self.cache_file: Path = self.cache_dir / "parser_cache.json"
        self._cache_data: dict[str, dict[str, Any]] | None = None
        self._metadata: CacheMetadata | None = None

        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._load_cache()

    def _load_cache(self) -> None:
        """キャッシュファイルを読み込む"""
        if not self.enabled:
            return

        if self.cache_file.exists():
            try:
                with open(self.cache_file, encoding="utf-8") as f:
                    loaded_data = json.load(f)
                    if isinstance(loaded_data, dict):
                        self._cache_data = loaded_data
                        logger.debug(
                            f"キャッシュを読み込みました: {len(self._cache_data)} エントリ"
                        )
                    else:
                        self._cache_data = {}
                        logger.warning("キャッシュファイルの形式が不正です")
            except (OSError, json.JSONDecodeError) as e:
                logger.warning(ErrorMessages.CACHE_LOAD_FAILED.format(error=e))
                self._cache_data = {}
        else:
            self._cache_data = {}

    def _save_cache(self) -> None:
        """キャッシュファイルを保存"""
        if not self.enabled or self._cache_data is None:
            return

        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache_data, f, indent=2, ensure_ascii=False)
            logger.debug(f"キャッシュを保存しました: {len(self._cache_data)} エントリ")
        except OSError as e:
            logger.warning(f"キャッシュファイルの保存に失敗しました: {e}")

    def get_file_hash(self, file_path: Path) -> str:
        """
        ファイルのハッシュを計算

        Args:
            file_path: ファイルパス

        Returns:
            ファイルのSHA256ハッシュ（16進数文字列）
        """
        try:
            with open(file_path, "rb") as f:
                file_hash = hashlib.sha256()
                # 大きなファイルでも効率的に処理するため、チャンク単位で読み込む
                while chunk := f.read(8192):
                    file_hash.update(chunk)
                return file_hash.hexdigest()
        except OSError as e:
            logger.warning(f"ファイルのハッシュ計算に失敗しました ({file_path}): {e}")
            return ""

    def get_cache_key(self, file_path: Path, parser_type: str) -> str:
        """
        キャッシュキーを生成

        Args:
            file_path: ファイルパス（相対パスまたは絶対パス）
            parser_type: パーサーの種類（例: 'python', 'javascript'）

        Returns:
            キャッシュキー
        """
        try:
            # 相対パスに変換
            if file_path.is_absolute():
                file_path_relative = file_path.relative_to(self.project_root)
            else:
                file_path_relative = file_path

            # 正規化されたパス文字列を使用
            normalized_path = str(file_path_relative).replace("\\", "/")
            return f"{parser_type}:{normalized_path}"
        except ValueError:
            # プロジェクトルート外のファイルの場合、絶対パスを使用
            return f"{parser_type}:{file_path}"

    def get_cached_result(self, file_path: Path, parser_type: str) -> list[APIInfo] | None:
        """
        キャッシュから結果を取得

        Args:
            file_path: ファイルパス
            parser_type: パーサーの種類

        Returns:
            キャッシュされた結果（存在する場合）、またはNone
        """
        if not self.enabled or self._cache_data is None:
            return None

        if not file_path.exists():
            return None

        cache_key = self.get_cache_key(file_path, parser_type)
        cache_entry = self._cache_data.get(cache_key)

        if cache_entry is None:
            return None

        # まずmtimeをチェック（軽い処理）
        # mtimeが一致しない場合は、ハッシュ計算をスキップして早期リターン
        try:
            current_mtime = file_path.stat().st_mtime
        except OSError:
            # ファイルアクセスエラーの場合、キャッシュを無効化
            del self._cache_data[cache_key]
            return None

        cached_mtime = cache_entry.get("mtime")
        if current_mtime != cached_mtime:
            # mtimeが一致しない場合、キャッシュは無効
            logger.debug(f"キャッシュが無効（mtime不一致）: {file_path}")
            del self._cache_data[cache_key]
            return None

        # mtimeが一致する場合のみ、ハッシュを計算して検証（重い処理）
        # ハッシュが一致すれば、キャッシュは有効
        current_hash = self.get_file_hash(file_path)
        cached_hash = cache_entry.get("hash")

        if current_hash and current_hash == cached_hash:
            logger.debug(f"キャッシュから結果を取得: {file_path}")
            result = cache_entry.get("result")
            if result is None:
                return None
            # 辞書のリストをAPIInfoのリストに変換
            if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
                return [APIInfo(**item) if isinstance(item, dict) else item for item in result]
            return result

        # ハッシュが一致しない場合、キャッシュは無効
        logger.debug(f"キャッシュが無効（ハッシュ不一致）: {file_path}")
        del self._cache_data[cache_key]
        return None

    def set_cached_result(self, file_path: Path, parser_type: str, result: list[APIInfo]) -> None:
        """
        結果をキャッシュに保存

        Args:
            file_path: ファイルパス
            parser_type: パーサーの種類
            result: 解析結果
        """
        if not self.enabled or self._cache_data is None:
            return

        if not file_path.exists():
            return

        cache_key = self.get_cache_key(file_path, parser_type)
        file_hash = self.get_file_hash(file_path)

        try:
            file_mtime = file_path.stat().st_mtime
        except OSError:
            return

        # APIInfoオブジェクトを辞書に変換して保存
        result_dicts = [api.model_dump() if isinstance(api, APIInfo) else api for api in result]
        self._cache_data[cache_key] = {
            "hash": file_hash,
            "mtime": file_mtime,
            "result": result_dicts,
            "cached_at": datetime.now().isoformat(),
        }

    def clear_cache(self) -> None:
        """キャッシュをクリア"""
        if self._cache_data is not None:
            self._cache_data.clear()
            self._save_cache()
            logger.info("キャッシュをクリアしました")

    def invalidate_file(self, file_path: Path, parser_type: str | None = None) -> None:
        """
        特定のファイルのキャッシュを無効化

        Args:
            file_path: ファイルパス
            parser_type: パーサーの種類（Noneの場合はすべてのパーサータイプ）
        """
        if not self.enabled or self._cache_data is None:
            return

        if parser_type:
            cache_key = self.get_cache_key(file_path, parser_type)
            if cache_key in self._cache_data:
                del self._cache_data[cache_key]
                logger.debug(f"キャッシュを無効化: {file_path} ({parser_type})")
        else:
            # すべてのパーサータイプのキャッシュを無効化
            try:
                # 相対パスに変換
                if file_path.is_absolute():
                    file_path_relative = file_path.relative_to(self.project_root)
                else:
                    file_path_relative = file_path
                normalized_path = str(file_path_relative).replace("\\", "/")
            except ValueError:
                # プロジェクトルート外のファイルの場合、絶対パスを使用
                normalized_path = str(file_path).replace("\\", "/")

            keys_to_remove = [
                key for key in self._cache_data.keys() if key.endswith(f":{normalized_path}")
            ]
            for key in keys_to_remove:
                del self._cache_data[key]
                logger.debug(f"キャッシュを無効化: {file_path}")

    def save(self) -> None:
        """キャッシュを保存（明示的に保存する場合）"""
        self._save_cache()

    def get_cache_stats(self) -> dict[str, Any]:
        """
        キャッシュの統計情報を取得

        Returns:
            統計情報の辞書
        """
        if not self.enabled or self._cache_data is None:
            return {"enabled": False, "total_entries": 0, "cache_file_size": 0}

        cache_file_size = self.cache_file.stat().st_size if self.cache_file.exists() else 0

        return {
            "enabled": True,
            "total_entries": len(self._cache_data),
            "cache_file_size": cache_file_size,
            "cache_file_path": str(self.cache_file),
        }
