"""
Markdown chunking strategy.
"""

from pathlib import Path
from typing import Any

from .base_strategy import BaseChunkStrategy


class MarkdownChunkStrategy(BaseChunkStrategy):
    """Strategy for chunking Markdown files."""

    def chunk(self, content: str, file_path: Path) -> list[dict[str, Any]]:
        """Chunk Markdown files by headers."""
        chunks = []
        lines = content.splitlines()

        current_section: list[str] = []
        section_start = 0
        header_name = "Introduction"

        for i, line in enumerate(lines):
            # Detect header lines (starting with #)
            if line.startswith("#"):
                # Save previous section
                if current_section:
                    section_text = "\n".join(current_section)
                    chunks.append(
                        {
                            "file": str(file_path.relative_to(self.project_root)),
                            "type": "MarkdownSection",
                            "name": header_name,
                            "text": section_text,
                            "start_line": section_start + 1,
                            "end_line": i,
                            "hash": self._hash_text(section_text),
                        }
                    )

                # Start new section
                header_name = line.lstrip("#").strip()
                section_start = i
                current_section = [line]
            else:
                current_section.append(line)

        # Save last section
        if current_section:
            section_text = "\n".join(current_section)
            chunks.append(
                {
                    "file": str(file_path.relative_to(self.project_root)),
                    "type": "MarkdownSection",
                    "name": header_name,
                    "text": section_text,
                    "start_line": section_start + 1,
                    "end_line": len(lines),
                    "hash": self._hash_text(section_text),
                }
            )

        return chunks
