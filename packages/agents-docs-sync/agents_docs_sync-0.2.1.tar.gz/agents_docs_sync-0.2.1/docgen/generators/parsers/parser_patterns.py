"""Common parsing patterns for code parsers."""

from pathlib import Path
import re

from ...models.api import APIInfo


class ParserPatterns:
    """Common patterns and utilities for code parsing."""

    # Common comment patterns
    DOCSTRING_PATTERNS = {
        "python": [
            (r'""".*?"""', re.DOTALL),  # Triple double quotes
            (r"'''.*?'''", re.DOTALL),  # Triple single quotes
        ],
        "javascript": [
            (r"/\*\*.*?\*/", re.DOTALL),  # JSDoc comments
        ],
        "typescript": [
            (r"/\*\*.*?\*/", re.DOTALL),  # JSDoc comments
        ],
    }

    # Common function/class patterns
    FUNCTION_PATTERNS = {
        "python": [
            (r"def\s+(\w+)\s*\(", "function"),
            (r"class\s+(\w+)", "class"),
            (r"async\s+def\s+(\w+)\s*\(", "function"),
        ],
        "javascript": [
            (r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(", "function"),
            (r"(?:export\s+)?class\s+(\w+)", "class"),
            (
                r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>",
                "function",
            ),
        ],
        "typescript": [
            (r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(", "function"),
            (r"(?:export\s+)?class\s+(\w+)", "class"),
            (
                r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>",
                "function",
            ),
            (r"(?:export\s+)?(\w+)\s*\([^)]*\)\s*:", "function"),  # Method definitions
        ],
    }

    @classmethod
    def extract_docstring(cls, content: str, language: str, start_pos: int) -> str | None:
        """
        Extract docstring/comment from content starting at a position.

        Args:
            content: Source code content
            language: Programming language
            start_pos: Position to start searching from

        Returns:
            Extracted docstring or None
        """
        patterns = cls.DOCSTRING_PATTERNS.get(language, [])
        for pattern, flags in patterns:
            regex = re.compile(pattern, flags)
            match = regex.search(content, start_pos)
            if match and match.start() <= start_pos + 10:  # Within reasonable distance
                return match.group(0).strip()
        return None

    @classmethod
    def find_functions_and_classes(cls, content: str, language: str) -> list[tuple[str, str, int]]:
        """
        Find all functions and classes in content.

        Args:
            content: Source code content
            language: Programming language

        Returns:
            List of (name, type, position) tuples
        """
        results = []
        patterns = cls.FUNCTION_PATTERNS.get(language, [])

        for pattern, entity_type in patterns:
            regex = re.compile(pattern, re.MULTILINE)
            for match in regex.finditer(content):
                name = match.group(1)
                position = match.start()
                results.append((name, entity_type, position))

        return results

    @classmethod
    def create_api_info(
        cls,
        name: str,
        entity_type: str,
        file_path: Path,
        project_root: Path,
        line_number: int | None = None,
        signature: str | None = None,
        docstring: str | None = None,
        language: str | None = None,
    ) -> APIInfo:
        """
        Create APIInfo object with common fields.

        Args:
            name: Function/class name
            entity_type: Type ('function', 'class', etc.)
            file_path: Source file path
            project_root: Project root path
            line_number: Line number (optional)
            signature: Function signature (optional)
            docstring: Documentation string (optional)
            language: Programming language (optional, inferred from file extension if not provided)

        Returns:
            APIInfo object
        """
        relative_path = file_path.relative_to(project_root)

        # 言語を推測（拡張子から）
        if language is None:
            ext_to_lang = {
                ".py": "python",
                ".js": "javascript",
                ".jsx": "javascript",
                ".ts": "typescript",
                ".tsx": "typescript",
                ".go": "go",
                ".rs": "rust",
                ".java": "java",
                ".cpp": "cpp",
                ".c": "c",
            }
            language = ext_to_lang.get(file_path.suffix.lower(), "unknown")

        return APIInfo(
            name=name,
            type=entity_type,
            file_path=str(relative_path),
            line_number=line_number,
            signature=signature,
            docstring=docstring,
            language=language,
        )

    @classmethod
    def clean_docstring(cls, docstring: str, language: str) -> str:
        """
        Clean and normalize docstring content.

        Args:
            docstring: Raw docstring
            language: Programming language

        Returns:
            Cleaned docstring
        """
        if language in ["python"]:
            # Remove triple quotes
            docstring = re.sub(r'"""|"""', "", docstring)
            docstring = re.sub(r"'''|'''", "", docstring)
        elif language in ["javascript", "typescript"]:
            # Remove JSDoc markers
            docstring = re.sub(r"/\*\*|\*/", "", docstring)

        # Clean up whitespace
        lines = docstring.strip().split("\n")
        cleaned_lines = []
        for line in lines:
            # Remove common prefixes
            line = re.sub(r"^\s*\*\s*", "", line)  # Remove * prefixes
            line = re.sub(r"^\s*#\s*", "", line)  # Remove # prefixes
            cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()
