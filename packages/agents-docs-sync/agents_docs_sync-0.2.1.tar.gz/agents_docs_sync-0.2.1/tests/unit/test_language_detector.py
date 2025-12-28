"""
言語検出モジュールのテスト
"""

from unittest.mock import MagicMock

from docgen.detectors.detector_patterns import DetectorPatterns
from docgen.language_detector import LanguageDetector


class TestLanguageDetector:
    """LanguageDetectorクラスのテスト"""

    def test_init(self, tmp_path):
        """初期化テスト"""
        detector = LanguageDetector(tmp_path)
        assert detector.project_root == tmp_path
        assert detector.detected_languages == []
        assert detector.detected_package_managers == {}

    def test_detect_languages_python(self, tmp_path):
        """Python言語検出テスト"""
        # Pythonファイルを作成
        (tmp_path / "main.py").write_text("print('hello')")

        detector = LanguageDetector(tmp_path)
        languages = detector.detect_languages(use_parallel=False)
        language_names = [lang.name for lang in languages]

        assert "python" in language_names
        assert detector.get_detected_languages() == language_names

    def test_get_detected_package_managers(self, tmp_path):
        """パッケージマネージャ取得テスト"""
        detector = LanguageDetector(tmp_path)
        assert detector.get_detected_package_managers() == {}

    def test_ignored_languages(self, tmp_path):
        """languages.ignoredで指定された言語が検出結果から除外されるテスト"""
        # Pythonファイルを作成
        (tmp_path / "main.py").write_text("print('hello')")

        # モックのconfig_managerを作成
        mock_config_manager = MagicMock()
        mock_config_manager.load_detector_defaults.return_value = {}
        mock_config_manager.load_detector_user_overrides.return_value = {}
        mock_config_manager.merge_detector_configs.return_value = {}
        mock_config_manager.accessor.exclude_directories = []
        mock_config_manager.accessor.languages_ignored = ["python"]

        detector = LanguageDetector(tmp_path, config_manager=mock_config_manager)
        languages = detector.detect_languages(use_parallel=False)
        language_names = [lang.name for lang in languages]

        # Pythonは検出されるが、ignoredで除外される
        assert "python" not in language_names

    def test_exclude_directories_applied_to_detection(self, tmp_path):
        """exclude.directoriesが言語検出に適用されるテスト"""
        # 除外ディレクトリにPythonファイルを作成
        excluded_dir = tmp_path / "my_excluded_dir"
        excluded_dir.mkdir()
        (excluded_dir / "main.py").write_text("print('hello')")

        # キャッシュをクリア
        DetectorPatterns.clear_cache()

        # モックのconfig_managerを作成（my_excluded_dirを除外）
        mock_config_manager = MagicMock()
        mock_config_manager.load_detector_defaults.return_value = {}
        mock_config_manager.load_detector_user_overrides.return_value = {}
        mock_config_manager.merge_detector_configs.return_value = {}
        mock_config_manager.accessor.exclude_directories = ["my_excluded_dir"]
        mock_config_manager.accessor.languages_ignored = []

        detector = LanguageDetector(tmp_path, config_manager=mock_config_manager)
        languages = detector.detect_languages(use_parallel=False)
        language_names = [lang.name for lang in languages]

        # 除外ディレクトリ内のPythonファイルは検出されない
        assert "python" not in language_names

        # キャッシュをクリア（他のテストに影響しないように）
        DetectorPatterns.clear_cache()

    def test_exclude_directories_not_applied_to_non_excluded(self, tmp_path):
        """exclude.directoriesで除外されないディレクトリのファイルは検出されるテスト"""
        # 非除外ディレクトリにPythonファイルを作成
        normal_dir = tmp_path / "my_normal_dir"
        normal_dir.mkdir()
        (normal_dir / "main.py").write_text("print('hello')")

        # キャッシュをクリア
        DetectorPatterns.clear_cache()

        # モックのconfig_managerを作成（別のディレクトリを除外）
        mock_config_manager = MagicMock()
        mock_config_manager.load_detector_defaults.return_value = {}
        mock_config_manager.load_detector_user_overrides.return_value = {}
        mock_config_manager.merge_detector_configs.return_value = {}
        mock_config_manager.accessor.exclude_directories = ["other_excluded_dir"]
        mock_config_manager.accessor.languages_ignored = []

        detector = LanguageDetector(tmp_path, config_manager=mock_config_manager)
        languages = detector.detect_languages(use_parallel=False)
        language_names = [lang.name for lang in languages]

        # 非除外ディレクトリ内のPythonファイルは検出される
        assert "python" in language_names

        # キャッシュをクリア（他のテストに影響しないように）
        DetectorPatterns.clear_cache()
