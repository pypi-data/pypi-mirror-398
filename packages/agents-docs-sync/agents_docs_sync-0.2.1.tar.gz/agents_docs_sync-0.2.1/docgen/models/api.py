"""API related Pydantic models."""

from typing import Any

from pydantic import BaseModel, Field


class APIParameter(BaseModel):
    """APIパラメータモデル"""

    name: str = Field(description="パラメータ名")
    type: str = Field(description="パラメータの型")
    description: str | None = Field(default=None, description="パラメータの説明")
    default: Any = Field(default=None, description="デフォルト値")
    required: bool = Field(default=True, description="必須かどうか")


class APIInfo(BaseModel):
    """API情報モデル"""

    name: str = Field(description="関数/メソッド/クラスの名前")
    type: str = Field(description="種類 (function, method, class, etc.)")
    file_path: str = Field(description="ファイルパス")
    line_number: int | None = Field(default=None, description="行番号")
    signature: str | None = Field(default=None, description="シグネチャ")
    docstring: str | None = Field(default=None, description="ドキュメント文字列")
    parameters: list[APIParameter] | None = Field(default=None, description="パラメータ情報")
    return_type: str | None = Field(default=None, description="戻り値の型")
    decorators: list[str] | None = Field(default=None, description="デコレータ")
    visibility: str | None = Field(default=None, description="可視性 (public, private, protected)")
    language: str = Field(description="プログラミング言語")
