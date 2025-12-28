"""
Base chunking strategy.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseChunkStrategy(ABC):
    """Base class for chunking strategies."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    @abstractmethod
    def chunk(self, content: str, file_path: Path) -> list[dict[str, Any]]:
        """
        Chunk the content.

        Args:
            content: File content
            file_path: Path to the file

        Returns:
            List of chunks
        """
        pass

    def _hash_text(self, text: str) -> str:
        """Calculate hash of text for differential updates."""
        import hashlib

        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
