"""
Custom assertion helpers for tests
"""

from pathlib import Path


def assert_file_exists(file_path: Path, message: str = None):
    """
    Assert that a file exists

    Args:
        file_path: Path to the file
        message: Custom error message

    Raises:
        AssertionError: If file does not exist
    """
    msg = message or f"File should exist: {file_path}"
    assert file_path.exists(), msg
    assert file_path.is_file(), f"Path exists but is not a file: {file_path}"


def assert_file_contains(file_path: Path, content: str, message: str = None):
    """
    Assert that a file contains specific content

    Args:
        file_path: Path to the file
        content: Content that should be in the file
        message: Custom error message

    Raises:
        AssertionError: If file doesn't exist or doesn't contain content
    """
    assert file_path.exists(), f"File does not exist: {file_path}"
    file_content = file_path.read_text()
    msg = message or f"File should contain '{content}'"
    assert content in file_content, msg


def assert_markdown_valid(content: str):
    """
    Basic validation that markdown content is well-formed

    Args:
        content: Markdown content to validate

    Raises:
        AssertionError: If markdown is invalid
    """
    assert content.strip(), "Markdown content should not be empty"
    # Check for at least one header
    assert "#" in content, "Markdown should contain at least one header"
    # Check for balanced code blocks
    triple_backticks = content.count("```")
    assert triple_backticks % 2 == 0, "Code blocks should be balanced (```)"
