"""
ロギング設定モジュール
共通のロギング設定を提供します
"""

import logging
from pathlib import Path
import sys


def setup_logger(
    name: str = "docgen", level: str | None = None, log_file: Path | None = None
) -> logging.Logger:
    """
    ロガーを設定して返す

    Args:
        name: ロガー名
        level: ログレベル（'DEBUG', 'INFO', 'WARNING', 'ERROR'）
                Noneの場合は環境変数DOCGEN_LOG_LEVELから取得、それもなければ'INFO'
        log_file: ログファイルのパス（Noneの場合は標準出力のみ）

    Returns:
        設定済みのロガー
    """
    logger = logging.getLogger(name)

    # 既にハンドラーが設定されている場合はスキップ
    if logger.handlers:
        return logger

    # ログレベルの設定
    if level is None:
        import os

        level = os.environ.get("DOCGEN_LOG_LEVEL", "INFO").upper()

    log_level = getattr(logging, level, logging.INFO)
    logger.setLevel(log_level)

    # フォーマッターの設定
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 標準出力ハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # テスト時はプロパゲーションを有効にする
    import os

    if os.environ.get("DOCGEN_TESTING"):
        logger.propagate = True
    else:
        logger.propagate = False

    # ファイルハンドラー（指定されている場合）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """
    ロガーを取得する（既に設定されている場合はそれを返す）

    Args:
        name: ロガー名（Noneの場合は'docgen'）

    Returns:
        ロガー
    """
    logger_name = name or "docgen"
    logger = logging.getLogger(logger_name)

    # ハンドラーが設定されていない場合は設定
    if not logger.handlers:
        return setup_logger(logger_name)

    return logger
