"""
CLIモジュールのテスト
"""

import os
from unittest.mock import patch

from docgen.docgen import run_cli
from docgen.models import DetectedLanguage


class TestCLI:
    """CLI関数のテスト"""

    @patch("docgen.DocGen")
    def test_run_detect_only(self, mock_docgen_class, tmp_path):
        """言語検出のみ実行テスト"""
        mock_docgen = mock_docgen_class.return_value
        mock_docgen.detect_languages.return_value = [DetectedLanguage(name="python")]

        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = type(
                "Args",
                (),
                {
                    "command": None,
                    "detect_only": True,
                    "no_readme": False,
                    "no_api_doc": False,
                    "config": None,
                    "build_index": False,
                    "use_rag": False,
                    "generate_arch": False,
                    "quiet": False,
                },
            )()

            with patch("pathlib.Path.cwd", return_value=tmp_path):
                result = run_cli()
                assert result == 0
                mock_docgen.detect_languages.assert_called_once()

    def test_init_command_creates_config(self, tmp_path):
        """initコマンドが設定ファイルを作成することを確認"""

        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = type(
                "Args",
                (),
                {
                    "command": "init",
                    "force": False,
                    "quiet": False,
                },
            )()

            with patch("pathlib.Path.cwd", return_value=tmp_path):
                result = run_cli()
                assert result == 0
                assert (tmp_path / "docgen" / "config.toml").exists()

    def test_init_command_creates_all_directories(self, tmp_path):
        """initコマンドがすべてのディレクトリを作成することを確認"""

        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = type(
                "Args",
                (),
                {
                    "command": "init",
                    "force": False,
                    "quiet": False,
                },
            )()

            with patch("pathlib.Path.cwd", return_value=tmp_path):
                result = run_cli()
                assert result == 0
                assert (tmp_path / "docgen").exists()
                assert (tmp_path / "docgen" / "templates").exists()
                assert (tmp_path / "docgen" / "prompts").exists()
                assert (tmp_path / "docgen" / "hooks").exists()

    def test_init_command_copies_all_files(self, tmp_path):
        """initコマンドがすべてのファイルをコピーすることを確認"""

        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = type(
                "Args",
                (),
                {
                    "command": "init",
                    "force": False,
                    "quiet": False,
                },
            )()

            with patch("pathlib.Path.cwd", return_value=tmp_path):
                result = run_cli()
                assert result == 0

                # config.tomlが作成されている
                assert (tmp_path / "docgen" / "config.toml").exists()

                # templatesディレクトリにファイルが存在
                templates_dir = tmp_path / "docgen" / "templates"
                assert len(list(templates_dir.iterdir())) > 0

                # promptsディレクトリにファイルが存在
                prompts_dir = tmp_path / "docgen" / "prompts"
                assert len(list(prompts_dir.iterdir())) > 0

                # hooksディレクトリにファイルが存在
                hooks_dir = tmp_path / "docgen" / "hooks"
                assert len(list(hooks_dir.iterdir())) > 0

    def test_init_command_sets_hook_permissions(self, tmp_path):
        """initコマンドがhooksファイルに実行権限を付与することを確認"""

        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = type(
                "Args",
                (),
                {
                    "command": "init",
                    "force": False,
                    "quiet": False,
                },
            )()

            with patch("pathlib.Path.cwd", return_value=tmp_path):
                result = run_cli()
                assert result == 0

                # hooksディレクトリ内のファイルが実行可能
                hooks_dir = tmp_path / "docgen" / "hooks"
                for hook_file in hooks_dir.iterdir():
                    if hook_file.is_file():
                        # 実行権限があることを確認
                        assert os.access(hook_file, os.X_OK)

    def test_init_command_with_existing_config(self, tmp_path):
        """既存の設定ファイルがある場合に警告を表示することを確認"""

        # 既存の設定ファイルを作成
        docgen_dir = tmp_path / "docgen"
        docgen_dir.mkdir()
        config_file = docgen_dir / "config.toml"
        config_file.write_text('[project]\nname = "test"')

        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = type(
                "Args",
                (),
                {
                    "command": "init",
                    "force": False,
                    "quiet": False,
                },
            )()

            with patch("pathlib.Path.cwd", return_value=tmp_path):
                result = run_cli()
                # 既存ファイルがある場合は失敗
                assert result == 1
                # 元の内容が保持されていることを確認
                assert config_file.read_text() == '[project]\nname = "test"'

    def test_init_command_with_force_flag(self, tmp_path):
        """--forceフラグで既存ファイルを上書きすることを確認"""

        # 既存の設定ファイルを作成
        docgen_dir = tmp_path / "docgen"
        docgen_dir.mkdir()
        config_file = docgen_dir / "config.toml"
        config_file.write_text('[project]\nname = "test"')

        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = type(
                "Args",
                (),
                {
                    "command": "init",
                    "force": True,
                    "quiet": False,
                },
            )()

            with patch("pathlib.Path.cwd", return_value=tmp_path):
                result = run_cli()
                assert result == 0
                # 内容が上書きされていることを確認
                assert config_file.read_text() != '[project]\nname = "test"'

    @patch("docgen.DocGen")
    def test_auto_init_when_config_missing(self, mock_docgen_class, tmp_path):
        """config.tomlがない場合に自動初期化されることを確認"""
        mock_docgen = mock_docgen_class.return_value
        mock_docgen.detect_languages.return_value = [DetectedLanguage(name="python")]

        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = type(
                "Args",
                (),
                {
                    "command": None,
                    "detect_only": True,
                    "no_readme": False,
                    "no_api_doc": False,
                    "config": None,
                    "build_index": False,
                    "use_rag": False,
                    "generate_arch": False,
                    "quiet": False,
                },
            )()

            with patch("pathlib.Path.cwd", return_value=tmp_path):
                result = run_cli()
                assert result == 0
                # 自動的にconfig.tomlが作成されている
                assert (tmp_path / "docgen" / "config.toml").exists()

    @patch("docgen.DocGen")
    def test_no_auto_init_when_config_exists(self, mock_docgen_class, tmp_path):
        """config.tomlがある場合は自動初期化しないことを確認"""
        # 既存の設定ファイルを作成
        docgen_dir = tmp_path / "docgen"
        docgen_dir.mkdir()
        config_file = docgen_dir / "config.toml"
        config_file.write_text('[project]\nname = "test"')

        mock_docgen = mock_docgen_class.return_value
        mock_docgen.detect_languages.return_value = [DetectedLanguage(name="python")]

        with patch("argparse.ArgumentParser.parse_args") as mock_args:
            mock_args.return_value = type(
                "Args",
                (),
                {
                    "command": None,
                    "detect_only": True,
                    "no_api_doc": False,
                    "no_readme": False,
                    "config": None,
                    "build_index": False,
                    "use_rag": False,
                    "generate_arch": False,
                    "quiet": False,
                },
            )()

            with patch("pathlib.Path.cwd", return_value=tmp_path):
                result = run_cli()
                assert result == 0
                # 元の内容が保持されている
                assert config_file.read_text() == '[project]\nname = "test"'
