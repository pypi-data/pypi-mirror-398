"""
Code chunking strategy.
"""

import ast
from pathlib import Path
import re
from typing import Any

from ...utils.logger import get_logger
from .base_strategy import BaseChunkStrategy

logger = get_logger(__name__)


class CodeChunkStrategy(BaseChunkStrategy):
    """Strategy for chunking code files (Python, JavaScript/TypeScript, YAML, TOML)."""

    def chunk(self, content: str, file_path: Path) -> list[dict[str, Any]]:
        """
        Chunk code content based on file extension.
        """
        suffix = file_path.suffix.lower()
        if suffix == ".py":
            return self._chunk_python(content, file_path)
        elif suffix in {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".d.ts"}:
            return self._chunk_javascript(content, file_path)
        elif suffix in {".yaml", ".yml"}:
            return self._chunk_yaml(content, file_path)
        elif suffix == ".toml":
            return self._chunk_toml(content, file_path)
        else:
            # Fallback to generic chunking for other code files
            # Return as a single chunk to ensure content is indexed
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

    def _chunk_python(self, content: str, file_path: Path) -> list[dict[str, Any]]:
        """Chunk Python files by function and class."""
        chunks = []

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            # Fallback to treating as a single chunk (handled by caller or return single chunk here?)
            # Returning single chunk here seems appropriate as fallback
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

        lines = content.splitlines()

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start_line = node.lineno - 1  # 0-indexed
                end_line = node.end_lineno if node.end_lineno else start_line + 1

                # Extract node content
                chunk_text = "\n".join(lines[start_line:end_line])

                # Extract docstring and add to chunk text for better semantic search
                docstring = ast.get_docstring(node)
                enhanced_text = chunk_text

                if docstring:
                    # docstringをテキストの前に追加して、意味的検索を改善
                    enhanced_text = f"# {node.name}: {docstring}\n{chunk_text}"

                # 直前のコメントも含める（最大3行）
                comment_lines = []
                for i in range(max(0, start_line - 3), start_line):
                    line = lines[i].strip()
                    if line.startswith("#"):
                        comment_lines.append(lines[i])
                if comment_lines:
                    enhanced_text = "\n".join(comment_lines) + "\n" + enhanced_text

                chunks.append(
                    {
                        "file": str(file_path.relative_to(self.project_root)),
                        "type": node.__class__.__name__,
                        "name": node.name,
                        "text": enhanced_text,
                        "start_line": start_line + 1,  # 1-indexed for display
                        "end_line": end_line,
                        "hash": self._hash_text(enhanced_text),
                    }
                )

        return chunks

    def _chunk_javascript(self, content: str, file_path: Path) -> list[dict[str, Any]]:
        """Chunk JavaScript/TypeScript files by function, class, and interface."""
        chunks = []
        lines = content.splitlines()

        # 関数定義のパターン（関数宣言、アロー関数、メソッド）
        function_patterns = [
            r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(",
            r"(?:export\s+)?(?:async\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>",
            r"(?:export\s+)?(?:async\s+)?(\w+)\s*:\s*(?:async\s+)?\([^)]*\)\s*=>",
            r"(?:export\s+)?(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{",
        ]

        # クラス定義のパターン
        class_pattern = r"(?:export\s+)?class\s+(\w+)"

        # インターフェース/型定義のパターン（TypeScript）
        interface_pattern = r"(?:export\s+)?(?:interface|type)\s+(\w+)"

        # 関数とクラスを抽出
        found_elements: list[dict[str, Any]] = []

        # クラス定義を抽出
        for match in re.finditer(class_pattern, content, re.MULTILINE):
            name = match.group(1)
            start_line = content[: match.start()].count("\n") + 1
            # 対応する}を見つける
            brace_count = 0
            end_pos = match.end()
            for i, char in enumerate(content[end_pos:], end_pos):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end_line = content[: i + 1].count("\n") + 1
                        found_elements.append(
                            {
                                "type": "ClassDef",
                                "name": name,
                                "start_line": start_line,
                                "end_line": end_line,
                            }
                        )
                        break

        # 関数定義を抽出
        for pattern in function_patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                name = match.group(1)
                if name:
                    start_line = content[: match.start()].count("\n") + 1
                    # 対応する}を見つける
                    brace_count = 0
                    end_pos = match.end()
                    for i, char in enumerate(content[end_pos:], end_pos):
                        if char == "{":
                            brace_count += 1
                        elif char == "}":
                            brace_count -= 1
                            if brace_count == 0:
                                end_line = content[: i + 1].count("\n") + 1
                                # 既に追加されていないかチェック
                                if not any(
                                    e["name"] == name and e["start_line"] == start_line
                                    for e in found_elements
                                ):
                                    found_elements.append(
                                        {
                                            "type": "FunctionDef",
                                            "name": name,
                                            "start_line": start_line,
                                            "end_line": end_line,
                                        }
                                    )
                                break

        # インターフェース/型定義を抽出（TypeScript）
        for match in re.finditer(interface_pattern, content, re.MULTILINE):
            name = match.group(1)
            start_line = content[: match.start()].count("\n") + 1
            # 対応する}を見つける
            brace_count = 0
            end_pos = match.end()
            for i, char in enumerate(content[end_pos:], end_pos):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        end_line = content[: i + 1].count("\n") + 1
                        found_elements.append(
                            {
                                "type": "InterfaceDef",
                                "name": name,
                                "start_line": start_line,
                                "end_line": end_line,
                            }
                        )
                        break

        # チャンクを作成
        for elem in found_elements:
            start_line = elem.get("start_line", 1)
            end_line = elem.get("end_line", 1)
            if not isinstance(start_line, int) or not isinstance(end_line, int):
                continue
            start_idx = start_line - 1  # 0-indexed
            end_idx = end_line
            chunk_text = "\n".join(lines[start_idx:end_idx])

            chunks.append(
                {
                    "file": str(file_path.relative_to(self.project_root)),
                    "type": elem["type"],
                    "name": elem["name"],
                    "text": chunk_text,
                    "start_line": elem["start_line"],
                    "end_line": elem["end_line"],
                    "hash": self._hash_text(chunk_text),
                }
            )

        # 要素が見つからない場合はファイル全体を1つのチャンクとして返す
        if not chunks:
            return [
                {
                    "file": str(file_path.relative_to(self.project_root)),
                    "type": "File",
                    "name": file_path.name,
                    "text": content,
                    "start_line": 1,
                    "end_line": len(lines),
                    "hash": self._hash_text(content),
                }
            ]

        return chunks

    def _chunk_yaml(self, content: str, file_path: Path) -> list[dict[str, Any]]:
        """Chunk YAML files by top-level keys."""
        chunks = []
        lines = content.splitlines()

        current_section: list[str] = []
        section_start = 0
        section_name = "preamble"

        for i, line in enumerate(lines):
            # Detect top-level keys (no indent)
            if line and not line.startswith(" ") and ":" in line:
                # Save previous section
                if current_section:
                    section_text = "\n".join(current_section)
                    chunks.append(
                        {
                            "file": str(file_path.relative_to(self.project_root)),
                            "type": "YAMLSection",
                            "name": section_name,
                            "text": section_text,
                            "start_line": section_start + 1,
                            "end_line": i,
                            "hash": self._hash_text(section_text),
                        }
                    )

                # Start new section
                section_name = line.split(":")[0].strip()
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
                    "type": "YAMLSection",
                    "name": section_name,
                    "text": section_text,
                    "start_line": section_start + 1,
                    "end_line": len(lines),
                    "hash": self._hash_text(section_text),
                }
            )

        return chunks

    def _chunk_toml(self, content: str, file_path: Path) -> list[dict[str, Any]]:
        """Chunk TOML files by sections."""
        chunks = []
        lines = content.splitlines()

        current_section: list[str] = []
        section_start = 0
        section_name = "header"

        for i, line in enumerate(lines):
            # Detect section headers ([section])
            if line.strip().startswith("[") and line.strip().endswith("]"):
                # Save previous section
                if current_section:
                    section_text = "\n".join(current_section)
                    chunks.append(
                        {
                            "file": str(file_path.relative_to(self.project_root)),
                            "type": "TOMLSection",
                            "name": section_name,
                            "text": section_text,
                            "start_line": section_start + 1,
                            "end_line": i,
                            "hash": self._hash_text(section_text),
                        }
                    )

                # Start new section
                section_name = line.strip("[").strip("]")
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
                    "type": "TOMLSection",
                    "name": section_name,
                    "text": section_text,
                    "start_line": section_start + 1,
                    "end_line": len(lines),
                    "hash": self._hash_text(section_text),
                }
            )

        return chunks
