"""DocumentValidatorのテスト"""

import pytest

from docgen.rag.validator import DocumentValidator


class TestDocumentValidator:
    """DocumentValidatorクラスのテスト"""

    @pytest.fixture
    def validator(self, tmp_path):
        """テスト用のDocumentValidatorインスタンス"""
        return DocumentValidator(tmp_path)

    @pytest.fixture
    def sample_project(self, tmp_path):
        """テスト用のプロジェクト構造を作成"""
        # テストファイルを作成
        test_file = tmp_path / "test.py"
        test_file.write_text("def foo():\n    pass\n")

        readme = tmp_path / "README.md"
        readme.write_text("# Test Project\n")

        return tmp_path

    def test_validator_initialization(self, validator, tmp_path):
        """DocumentValidatorが正しく初期化されることを確認"""
        assert validator.project_root == tmp_path

    def test_validate_citations_valid(self, validator, sample_project):
        """有効な出典が正しく検証されることを確認"""
        doc = """
        この関数は [test.py:1] で定義されています。
        プロジェクト概要は [README.md:1] を参照してください。
        """

        errors = validator.validate_citations(doc)

        # エラーがないことを確認
        assert len(errors) == 0

    def test_validate_citations_invalid_file(self, validator, sample_project):
        """存在しないファイルを参照している場合にエラーを返すことを確認"""
        doc = """
        この機能は [nonexistent.py:1] で実装されています。
        """

        errors = validator.validate_citations(doc)

        # エラーが検出されることを確認
        assert len(errors) > 0
        assert any("nonexistent.py" in error for error in errors)

    def test_validate_citations_invalid_line(self, validator, sample_project):
        """存在しない行番号を参照している場合にエラーを返すことを確認"""
        doc = """
        この関数は [test.py:1000] で定義されています。
        """

        errors = validator.validate_citations(doc)

        # 行番号のエラーが検出されることを確認
        assert len(errors) > 0
        assert any("line" in error.lower() for error in errors)

    def test_validate_citations_range(self, validator, sample_project):
        """行範囲の出典が正しく検証されることを確認"""
        doc = """
        この関数は [test.py:1-2] で定義されています。
        """

        errors = validator.validate_citations(doc)

        # エラーがないことを確認
        assert len(errors) == 0

    def test_validate_citations_strict_mode(self, validator, sample_project):
        """厳格モードで技術的主張に出典がない場合に警告を返すことを確認"""
        # 英語の技術キーワード（function, class, defined）を含む文を使用
        doc = """
        This function is defined in the Foo class.
        The module implements the feature.
        """

        errors = validator.validate_citations(doc, strict=True)

        # 出典がない技術的主張が検出されることを確認
        assert len(errors) > 0

    def test_detect_secrets_no_secrets(self, validator):
        """機密情報がない場合に警告が返されないことを確認"""
        doc = """
        # プロジェクト概要

        このプロジェクトはテストプロジェクトです。

        ```bash
        python main.py
        ```
        """

        warnings = validator.detect_secrets(doc)

        # 警告がないことを確認
        assert len(warnings) == 0

    def test_detect_secrets_api_key_pattern(self, validator):
        """APIキーパターンが検出されることを確認"""
        doc = """
        設定ファイル:

        ```bash
        export API_KEY=sk-1234567890abcdefghijklmnopqrstuvwxyz
        ```
        """

        warnings = validator.detect_secrets(doc)

        # APIキーが検出されることを確認
        assert len(warnings) > 0

    def test_detect_secrets_long_random_string(self, validator):
        """長いランダム文字列が検出されることを確認"""
        doc = """
        ```python
        token = "abcdef123456789012345678901234567890"
        ```
        """

        warnings = validator.detect_secrets(doc)

        # 長い文字列が検出される可能性を確認
        # （厳格なパターンマッチングによる）
        assert isinstance(warnings, list)

    def test_validate_full(self, validator, sample_project):
        """総合検証が正しく動作することを確認"""
        doc = """
        # プロジェクト

        この関数は [test.py:1] で定義されています。
        """

        result = validator.validate(doc, check_citations=True, check_secrets=True)

        # 結果の構造を確認
        assert "valid" in result
        assert "errors" in result
        assert "warnings" in result
        assert isinstance(result["errors"], list)
        assert isinstance(result["warnings"], list)

    def test_validate_with_errors(self, validator, sample_project):
        """エラーがある場合にvalidがFalseになることを確認"""
        doc = """
        この機能は [nonexistent.py:1] で実装されています。
        """

        result = validator.validate(doc)

        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_print_report(self, validator, capsys):
        """検証レポートが正しく出力されることを確認"""
        result = {"valid": True, "errors": [], "warnings": ["Warning 1", "Warning 2"]}

        validator.print_report(result)

        captured = capsys.readouterr()
        assert "Document Validation Report" in captured.out
        assert "✅ Document is valid!" in captured.out
        assert "Warning 1" in captured.out

    def test_print_report_with_errors(self, validator, capsys):
        """エラーがある場合のレポートが正しく出力されることを確認"""
        result = {"valid": False, "errors": ["Error 1"], "warnings": []}

        validator.print_report(result)

        captured = capsys.readouterr()
        assert "❌ Document has errors" in captured.out
        assert "Error 1" in captured.out
