"""
アーキテクチャ生成 CLI
"""

import argparse
from pathlib import Path

from ..utils.logger import get_logger
from .renderer import ArchitectureRenderer
from .scanner import ProjectScanner

logger = get_logger("archgen")


def generate_architecture(
    project_root: Path,
    output_dir: Path,
    exclude_directories: list[str] | None = None,
) -> bool:
    """アーキテクチャを生成

    Args:
        project_root: プロジェクトルート
        output_dir: 出力ディレクトリ
        exclude_directories: スキャンから除外するディレクトリのリスト
    """
    try:
        logger.info(f"プロジェクトをスキャン中: {project_root}")
        scanner = ProjectScanner(project_root, exclude_directories=exclude_directories)
        manifest = scanner.scan()

        logger.info(f"検出されたサービス: {len(manifest.services)}")
        for service in manifest.services:
            logger.info(f"  - {service.name} ({service.type})")

        logger.info("アーキテクチャ図を生成中 (Mermaid)...")

        renderer = ArchitectureRenderer()
        outputs = renderer.render(manifest, output_dir)

        for fmt, path in outputs.items():
            logger.info(f"  ✓ {fmt}: {path}")

        logger.info("\n💡 生成された Mermaid 図は GitHub/GitLab で自動レンダリングされます")
        logger.info(f"   {outputs.get('markdown', '')} を確認してください")

        return True

    except Exception as e:
        logger.error(f"アーキテクチャ生成エラー: {e}", exc_info=True)
        return False


def main():
    """CLI エントリポイント"""
    parser = argparse.ArgumentParser(
        description="アーキテクチャ自動生成（Mermaid形式、システム依存なし）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  # Mermaid 形式で生成（デフォルト、依存なし）
  %(prog)s --root . --output docs/architecture
""",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="プロジェクトルート（デフォルト: カレントディレクトリ）",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/architecture"),
        help="出力ディレクトリ（デフォルト: docs/architecture）",
    )

    args = parser.parse_args()

    success = generate_architecture(args.root, args.output)
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
