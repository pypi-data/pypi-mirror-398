"""
ベンチマーク結果のデータモデル定義
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BenchmarkResult(BaseModel):
    """ベンチマーク測定結果"""

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
        }
    )

    name: str = Field(..., description="測定対象の処理名")
    duration: float = Field(..., description="実行時間（秒）")
    memory_peak: int = Field(..., description="ピークメモリ使用量（バイト）")
    memory_delta: int = Field(..., description="メモリ増加量（バイト）")
    cpu_percent: float = Field(default=0.0, description="CPU使用率（%）")
    timestamp: datetime = Field(default_factory=datetime.now, description="測定日時")
    children: list["BenchmarkResult"] = Field(default_factory=list, description="子処理の測定結果")
    metadata: dict[str, Any] = Field(default_factory=dict, description="追加メタデータ")


class BenchmarkSummary(BaseModel):
    """ベンチマーク結果の集計情報"""

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
        }
    )

    total_duration: float = Field(..., description="総実行時間（秒）")
    total_results: int = Field(..., description="測定結果の総数")
    memory_peak_total: int = Field(..., description="全体のピークメモリ使用量（バイト）")
    cpu_avg: float = Field(..., description="平均CPU使用率（%）")
    results: list[BenchmarkResult] = Field(default_factory=list, description="測定結果のリスト")
    bottlenecks: list[str] = Field(default_factory=list, description="ボトルネックのリスト")
