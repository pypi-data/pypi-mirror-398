"""
Text chunking strategy.
"""

from pathlib import Path
from typing import Any

from .base_strategy import BaseChunkStrategy


class TextChunkStrategy(BaseChunkStrategy):
    """Strategy for chunking generic text files."""

    def chunk(self, content: str, file_path: Path) -> list[dict[str, Any]]:
        """Chunk generic files as a single chunk."""
        return [
            {
                "file": str(file_path.relative_to(self.project_root)),
                "type": "File",
                "name": file_path.name,
                "text": content,
                "start_line": 1,
                "end_line": len(content.splitlines()),
                "hash": self._hash_text(content),
            }
        ]
