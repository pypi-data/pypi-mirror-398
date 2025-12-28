"""
Unit test fixtures
"""

import pytest


@pytest.fixture(scope="function")
def mock_file_system(mocker, tmp_path):
    """
    Mock file system operations for unit tests

    Returns:
        Path: Temporary directory for file operations
    """
    return tmp_path
