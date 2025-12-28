"""
各種検出器モジュール
"""

from .docker_detector import DockerDetector
from .python_detector import PythonDetector

__all__ = ["PythonDetector", "DockerDetector"]
