"""
DocumentGeneratorのテスト
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from docgen.document_generator import DocumentGenerator
from docgen.models import DetectedLanguage


class TestDocumentGenerator:
    """DocumentGeneratorクラスのテスト"""

    def test_document_generator_initialization(self, temp_project):
        """DocumentGeneratorの初期化テスト"""
        config = {"generation": {"generate_api_doc": True}}

        generator = DocumentGenerator(temp_project, [DetectedLanguage(name="python")], config)

        assert generator.project_root == temp_project
        assert len(generator.detected_languages) == 1
        assert generator.detected_languages[0].name == "python"
        assert generator.config == config

    def test_generate_documents_no_languages(self, temp_project, caplog):
        """言語がない場合のテスト"""
        config = {"generation": {"generate_api_doc": True}}

        generator = DocumentGenerator(temp_project, [], config)
        result = generator.generate_documents()

        assert result is False
        assert "サポートされている言語が検出されませんでした" in caplog.text

    @patch("docgen.document_generator.GeneratorFactory")
    def test_generate_documents_success(self, mock_factory, temp_project, caplog):
        """ドキュメント生成成功テスト"""
        config = {
            "generation": {
                "generate_api_doc": True,
                "update_readme": True,
                "generate_agents_doc": True,
            }
        }

        # モックの設定
        mock_generator = MagicMock()
        mock_generator.generate.return_value = True
        mock_factory.create_generator.return_value = mock_generator

        generator = DocumentGenerator(temp_project, [DetectedLanguage(name="python")], config)
        result = generator.generate_documents()

        assert result is True
        assert mock_factory.create_generator.call_count == 3
        assert "[APIドキュメント生成]" in caplog.text
        assert "[README生成]" in caplog.text
        assert "[AGENTS.md生成]" in caplog.text

    @patch("docgen.document_generator.GeneratorFactory")
    def test_generate_documents_partial_failure(self, mock_factory, temp_project, caplog):
        """部分的な失敗テスト"""
        config = {"generation": {"generate_api_doc": True, "update_readme": True}}

        # モックの設定 - 1つは成功、1つは失敗
        def side_effect(gen_type, project_root, languages, config, detected_package_managers):
            mock_gen = MagicMock()
            if gen_type == "api":
                mock_gen.generate.return_value = True
            else:
                mock_gen.generate.return_value = False
            return mock_gen

        mock_factory.create_generator.side_effect = side_effect

        generator = DocumentGenerator(temp_project, [DetectedLanguage(name="python")], config)
        result = generator.generate_documents()

        assert result is False  # 1つでも失敗したらFalse
        assert "✓ APIドキュメントを生成しました" in caplog.text
        assert "✗ READMEの生成に失敗しました" in caplog.text

    @patch("docgen.document_generator.GeneratorFactory")
    def test_generate_documents_exception(self, mock_factory, temp_project, caplog):
        """例外処理テスト"""
        config = {"generation": {"generate_api_doc": True}}

        # 例外を発生させる
        mock_factory.create_generator.side_effect = Exception("Test error")

        generator = DocumentGenerator(temp_project, [DetectedLanguage(name="python")], config)
        result = generator.generate_documents()

        assert result is False
        assert "✗ APIドキュメントの生成中にエラーが発生しました: Test error" in caplog.text

    @patch("docgen.document_generator.GeneratorFactory")
    def test_generate_documents_disabled_generators(self, mock_factory, temp_project):
        """ジェネレーターが無効な場合のテスト"""
        config = {
            "generation": {
                "generate_api_doc": False,
                "update_readme": False,
                "generate_agents_doc": False,
            }
        }

        generator = DocumentGenerator(temp_project, [DetectedLanguage(name="python")], config)
        result = generator.generate_documents()

        assert result is True  # 何も実行しないので成功
        mock_factory.create_generator.assert_not_called()

    @patch("docgen.document_generator.GeneratorFactory")
    def test_generate_documents_only_api(self, mock_factory, temp_project, caplog):
        """APIドキュメントのみ生成テスト"""
        config = {
            "generation": {
                "generate_api_doc": True,
                "update_readme": False,
                "generate_agents_doc": False,
            }
        }

        mock_generator = MagicMock()
        mock_generator.generate.return_value = True
        mock_factory.create_generator.return_value = mock_generator

        generator = DocumentGenerator(temp_project, [DetectedLanguage(name="python")], config)
        result = generator.generate_documents()

        assert result is True
        assert mock_factory.create_generator.call_count == 1
        assert "[APIドキュメント生成]" in caplog.text
        assert "[README生成]" not in caplog.text
        assert "[AGENTS.md生成]" not in caplog.text
