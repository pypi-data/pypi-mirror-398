import pytest

from docgen.collectors.structure_analyzer import StructureAnalyzer


class TestStructureAnalyzerExclude:
    """StructureAnalyzerのexclude機能のテスト"""

    @pytest.fixture
    def mock_project_root(self, tmp_path):
        """モック用のプロジェクトルートを作成"""
        # 作成する構造:
        # project_root/
        #   src/
        #     main.py
        #   exclude_me/
        #     secret.py
        #   keep_me/
        #     visible.py
        #   config.json

        root = tmp_path / "project"
        root.mkdir()

        (root / "src").mkdir()
        (root / "src" / "main.py").write_text(
            "class Main:\n    def m1(self): pass\n    def m2(self): pass\n    def m3(self): pass\n    def m4(self): pass\n    def m5(self): pass\n    def m6(self): pass"
        )

        (root / "exclude_me").mkdir()
        (root / "exclude_me" / "secret.py").write_text(
            "class Secret:\n    def s1(self): pass\n    def s2(self): pass\n    def s3(self): pass\n    def s4(self): pass\n    def s5(self): pass\n    def s6(self): pass"
        )

        (root / "keep_me").mkdir()
        (root / "keep_me" / "visible.py").write_text(
            "class Visible:\n    def v1(self): pass\n    def v2(self): pass\n    def v3(self): pass\n    def v4(self): pass\n    def v5(self): pass\n    def v6(self): pass"
        )

        (root / "config.json").write_text("{}")

        return root

    def test_default_exclude(self, mock_project_root):
        """デフォルトの除外設定のテスト"""
        analyzer = StructureAnalyzer(mock_project_root)
        structure = analyzer.analyze()

        assert "src/" in structure
        assert "exclude_me/" in structure
        assert "keep_me/" in structure
        assert "config.json" in structure

    def test_custom_exclude(self, mock_project_root):
        """カスタム除外設定のテスト"""
        exclude_dirs = ["exclude_me"]
        analyzer = StructureAnalyzer(mock_project_root, exclude_directories=exclude_dirs)
        structure = analyzer.analyze()

        assert "src/" in structure
        assert "exclude_me/" not in structure
        assert "keep_me/" in structure
        assert "config.json" in structure

    def test_custom_exclude_nested(self, mock_project_root):
        """ネストされた除外設定のテスト"""
        # analyzeメソッドはルート直下のディレクトリ名でフィルタリングするため、
        # "exclude_me" を指定すれば除外されるはず。
        # もし "src/exclude_me" のような指定が必要なら、実装を確認する必要があるが、
        # 今回の修正は `item.name in self.ignore_dirs` なので、ディレクトリ名での完全一致。

        exclude_dirs = ["exclude_me"]
        analyzer = StructureAnalyzer(mock_project_root, exclude_directories=exclude_dirs)
        structure = analyzer.analyze()

        assert "exclude_me/" not in structure
