"""
ベンチマークユーティリティ関数
"""

import os

import psutil


def get_current_process() -> psutil.Process:
    """
    現在のプロセスを取得

    Returns:
        現在のプロセス
    """
    return psutil.Process(os.getpid())


def format_duration(seconds: float) -> str:
    """
    実行時間をフォーマット

    Args:
        seconds: 秒数

    Returns:
        フォーマットされた文字列
    """
    if seconds < 0.001:
        return f"{seconds * 1000000:.2f}μs"
    elif seconds < 1.0:
        return f"{seconds * 1000:.2f}ms"
    else:
        return f"{seconds:.2f}s"


def format_memory(bytes_size: int) -> str:
    """
    メモリサイズをフォーマット

    Args:
        bytes_size: バイト数

    Returns:
        フォーマットされた文字列
    """
    size = float(bytes_size)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"
