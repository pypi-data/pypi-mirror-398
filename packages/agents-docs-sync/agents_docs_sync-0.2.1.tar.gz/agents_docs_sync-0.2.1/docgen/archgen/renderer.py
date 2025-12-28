"""
アーキテクチャ図のレンダリング管理
"""

from pathlib import Path

from .generators.mermaid_generator import MermaidGenerator
from .models import ArchitectureManifest


class ArchitectureRenderer:
    """アーキテクチャ図のレンダリングを管理"""

    def __init__(self, generator_type: str = "mermaid", image_formats: list[str] | None = None):
        """
        初期化

        Args:
            generator_type: 生成器の種類 ("mermaid", "blockdiag", "matplotlib")
            image_formats: 画像出力形式のリスト
        """
        self.generator_type = generator_type
        self.image_formats = image_formats or ["png"]

        # 現時点ではMermaidのみサポート
        self.generator = MermaidGenerator()

    def render(self, manifest: ArchitectureManifest, output_dir: Path) -> dict[str, Path]:
        """図を生成

        Args:
            manifest: アーキテクチャマニフェスト
            output_dir: 出力ディレクトリ

        Returns:
            生成されたファイルのパス辞書
        """
        outputs = {}

        # Mermaid で生成
        mermaid_path = self.generator.generate(manifest, output_dir)
        outputs["mermaid"] = mermaid_path
        outputs["markdown"] = output_dir / "architecture_diagram.md"

        # マニフェストも保存
        manifest_path = output_dir / "architecture_manifest.yml"
        manifest.to_yaml(manifest_path)
        outputs["manifest"] = manifest_path

        return outputs
