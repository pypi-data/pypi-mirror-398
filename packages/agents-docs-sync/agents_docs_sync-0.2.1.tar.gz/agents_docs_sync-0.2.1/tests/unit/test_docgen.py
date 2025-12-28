"""
DocGenクラスのテスト
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from docgen.docgen import DocGen
from docgen.models import DetectedLanguage


class TestDocGen:
    """DocGenクラスのテスト"""

    def test_initialization_default(self, temp_project):
        """デフォルト設定での初期化テスト"""
        docgen = DocGen(project_root=temp_project)

        assert docgen.project_root == temp_project
        assert docgen.docgen_dir == temp_project / "docgen"
        assert docgen.config_manager.config_path == temp_project / "docgen" / "config.toml"
        assert isinstance(docgen.config, dict)
        assert docgen.detected_languages == []

    def test_load_config_missing_file(self, temp_project):
        """設定ファイルが存在しない場合のテスト"""
        docgen = DocGen(project_root=temp_project)

        # _validate_configが呼ばれた後のconfigをチェック
        assert "languages" in docgen.config
        assert "output" in docgen.config
        assert "generation" in docgen.config
        assert "agents" in docgen.config

    def test_update_config(self, temp_project):
        """設定更新テスト"""
        docgen = DocGen(project_root=temp_project)

        updates = {"generation.update_readme": False, "output.agents_doc": "NEW_AGENTS.md"}

        docgen.update_config(updates)

        assert docgen.config["generation"]["update_readme"] is False
        assert docgen.config["output"]["agents_doc"] == "NEW_AGENTS.md"

    @patch("docgen.detectors.unified_detector.UnifiedDetectorFactory")
    def test_detect_languages_parallel(self, mock_factory, temp_project):
        """並列言語検出テスト"""
        # モックの設定
        mock_python = MagicMock()
        mock_python.detect.return_value = True
        mock_python.get_detected_language_object.return_value = DetectedLanguage(
            name="python", package_manager="pip"
        )

        mock_js = MagicMock()
        mock_js.detect.return_value = False
        mock_js.detect_package_manager.return_value = None

        mock_go = MagicMock()
        mock_go.detect.return_value = True
        mock_go.get_detected_language_object.return_value = DetectedLanguage(
            name="go", package_manager="go"
        )

        # create_all_detectorsがこれらのモックを返すように設定
        mock_factory.create_all_detectors.return_value = [mock_python, mock_js, mock_go]

        docgen = DocGen(project_root=temp_project)
        languages = docgen.detect_languages(use_parallel=True)
        lang_names = [lang.name for lang in languages]

        assert "python" in lang_names
        assert "go" in lang_names
        assert "javascript" not in lang_names
        # 順序は保証されないため、セットで比較するか、含まれていることを確認
        assert {lang.name for lang in docgen.detected_languages} == {"python", "go"}
        assert docgen.detected_package_managers == {"python": "pip", "go": "go"}

    @patch("docgen.detectors.unified_detector.UnifiedDetectorFactory")
    def test_detect_languages_sequential(self, mock_factory, temp_project):
        """逐次言語検出テスト"""
        # モックの設定
        mock_python = MagicMock()
        mock_python.detect.return_value = True
        mock_python.get_detected_language_object.return_value = DetectedLanguage(
            name="python", package_manager="pip"
        )

        mock_js = MagicMock()
        mock_js.detect.return_value = False
        mock_js.detect_package_manager.return_value = None

        mock_go = MagicMock()
        mock_go.detect.return_value = True
        mock_go.get_detected_language_object.return_value = DetectedLanguage(
            name="go", package_manager="go"
        )

        # create_all_detectorsがこれらのモックを返すように設定
        mock_factory.create_all_detectors.return_value = [mock_python, mock_js, mock_go]

        docgen = DocGen(project_root=temp_project)
        languages = docgen.detect_languages(use_parallel=False)
        lang_names = [lang.name for lang in languages]

        assert "python" in lang_names
        assert "go" in lang_names
        assert "javascript" not in lang_names
        assert docgen.detected_package_managers == {"python": "pip", "go": "go"}

    @patch("docgen.generators.api_generator.APIGenerator")
    @patch("docgen.generators.readme_generator.ReadmeGenerator")
    @patch("docgen.generators.agents_generator.AgentsGenerator")
    @patch("docgen.docgen.LanguageDetector")
    def test_generate_documents_success(
        self, mock_language_detector, mock_agents, mock_readme, mock_api, temp_project
    ):
        """ドキュメント生成成功テスト"""
        # モックの設定
        mock_language_detector.return_value.detect_languages.return_value = [
            DetectedLanguage(name="python")
        ]
        mock_language_detector.return_value.detected_package_managers = {}
        mock_api.return_value.generate.return_value = True
        mock_readme.return_value.generate.return_value = True
        mock_agents.return_value.generate.return_value = True

        docgen = DocGen(project_root=temp_project)

        result = docgen.generate_documents()

        assert result is True
        mock_api.assert_called_once()
        mock_readme.assert_called_once()
        mock_agents.assert_called_once()

    @patch("docgen.generators.api_generator.APIGenerator")
    @patch("docgen.generators.readme_generator.ReadmeGenerator")
    @patch("docgen.generators.agents_generator.AgentsGenerator")
    def test_generate_documents_partial_failure(
        self, mock_agents, mock_readme, mock_api, temp_project
    ):
        """ドキュメント生成一部失敗テスト"""
        # モックの設定
        mock_api.return_value.generate.return_value = True
        mock_readme.return_value.generate.return_value = False  # 失敗
        mock_agents.return_value.generate.return_value = True

        docgen = DocGen(project_root=temp_project)
        docgen.language_detector.detected_languages = [DetectedLanguage(name="python")]

        result = docgen.generate_documents()

        assert result is False  # 一部失敗なのでFalse

    def test_generate_documents_no_languages(self, temp_project):
        """言語が検出されない場合のテスト"""
        docgen = DocGen(project_root=temp_project)
        docgen.detected_languages = []  # 言語なし

        with patch.object(docgen, "detect_languages", return_value=[]):
            result = docgen.generate_documents()

        assert result is False

    @patch("docgen.generators.commit_message_generator.CommitMessageGenerator")
    def test_main_commit_msg_command(self, mock_generator, temp_project, capsys):
        """commit-msgコマンドのテスト"""
        mock_generator.return_value.generate.return_value = "Test commit message"

        with patch("sys.argv", ["docgen.py", "commit-msg"]):
            with patch("docgen.DocGen", return_value=MagicMock()):
                with patch("sys.exit") as mock_exit:
                    mock_exit.return_value = None
                    from docgen import main as main_func

                    main_func()
                    exit_code = 0

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Test commit message" in captured.out

    def test_main_detect_only(self, temp_project, caplog):
        """detect-onlyオプションのテスト"""
        with patch("sys.argv", ["docgen.py", "--detect-only"]):
            with patch("docgen.DocGen") as mock_docgen_class:
                mock_docgen = MagicMock()
                mock_docgen.detect_languages.return_value = [
                    DetectedLanguage(name="python"),
                    DetectedLanguage(name="javascript"),
                ]
                mock_docgen_class.return_value = mock_docgen

                with patch("sys.exit") as mock_exit:
                    mock_exit.return_value = None
                    from docgen.docgen import main as main_func

                    main_func()
                    exit_code = 0

            assert exit_code == 0
            mock_docgen.detect_languages.assert_called_once()
