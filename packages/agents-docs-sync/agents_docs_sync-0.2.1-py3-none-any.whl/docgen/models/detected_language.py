from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DetectedLanguage:
    """
    検出された言語の詳細情報を保持するクラス

    Attributes:
        name: 言語名 (例: 'python', 'javascript')
        version: 検出されたバージョン (例: '3.11', '18.0.0')
        package_manager: 使用されているパッケージマネージャ (例: 'poetry', 'npm')
        source_extensions: ソースコードの拡張子リスト (例: ['.py', '.pyi'])
        rag_enabled: RAGインデックスに含めるかどうか
        doc_config: ドキュメント生成に関する設定
    """

    name: str
    version: str | None = None
    package_manager: str | None = None
    source_extensions: list[str] = field(default_factory=list)
    # Metadata for RAG and Documentation
    rag_enabled: bool = True
    doc_config: dict[str, Any] = field(default_factory=dict)

    def get_rag_patterns(self) -> list[str]:
        """RAGインデックスに含めるためのglobパターンリストを取得"""
        return [f"*{ext}" for ext in self.source_extensions]
