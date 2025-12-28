"""
Integration test fixtures
"""

import pytest


@pytest.fixture(scope="function")
def full_project_setup(sample_project_root, mock_config):
    """
    Complete project setup for integration tests

    Returns:
        dict: Dictionary with project root and configuration
    """
    return {
        "root": sample_project_root,
        "config": mock_config,
    }
