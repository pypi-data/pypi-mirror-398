"""Cache related Pydantic models."""

from datetime import datetime

from pydantic import BaseModel, Field

from .api import APIInfo


class CacheEntry(BaseModel):
    """キャッシュエントリーモデル"""

    data: list[APIInfo] = Field(description="キャッシュされたAPI情報")
    timestamp: datetime = Field(description="キャッシュ作成時刻")
    file_hash: str = Field(description="ファイルハッシュ")
    parser_type: str = Field(description="パーサーの種類")


class CacheMetadata(BaseModel):
    """キャッシュメタデータモデル"""

    version: str = Field(default="1.0", description="キャッシュバージョン")
    created_at: datetime = Field(description="キャッシュ作成時刻")
    last_updated: datetime = Field(description="最終更新時刻")
    total_entries: int = Field(default=0, description="総エントリー数")
