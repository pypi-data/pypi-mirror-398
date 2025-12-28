"""
ConfigManagerのテスト
"""

from pathlib import Path
from unittest.mock import patch

# docgenモジュールをインポート可能にする
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
DOCGEN_DIR = PROJECT_ROOT / "docgen"

from docgen.config_manager import ConfigManager


class TestConfigManager:
    """ConfigManagerクラスのテスト"""

    def test_config_manager_initialization_with_config_path(self, temp_project):
        """設定ファイルパス指定での初期化テスト"""
        docgen_dir = temp_project / ".docgen"
        docgen_dir.mkdir()
        config_path = docgen_dir / "custom_config.toml"

        config_manager = ConfigManager(temp_project, docgen_dir, config_path)

        assert config_manager.project_root == temp_project
        assert config_manager.docgen_dir == docgen_dir
        assert config_manager.config_path == config_path

    def test_config_manager_initialization_default_config_path(self, temp_project):
        """デフォルト設定ファイルパスでの初期化テスト"""
        docgen_dir = temp_project / ".docgen"
        docgen_dir.mkdir()

        config_manager = ConfigManager(temp_project, docgen_dir)

        assert config_manager.config_path == docgen_dir / "config.toml"

    @patch("docgen.config_manager.safe_read_toml")
    def test_load_config_existing_file(self, mock_safe_read_toml, temp_project):
        """既存の設定ファイル読み込みテスト"""
        docgen_dir = temp_project / ".docgen"
        docgen_dir.mkdir()
        config_path = docgen_dir / "config.toml"
        config_path.touch()  # ファイルを作成

        # 有効な設定を使用（Pydanticバリデーションを通過する）
        test_config = {
            "languages": {"auto_detect": False, "preferred": ["python"]},
            "output": {
                "api_doc": "custom_api.md",
                "readme": "CUSTOM_README.md",
                "agents_doc": "CUSTOM_AGENTS.md",
            },
            "generation": {
                "update_readme": False,
                "generate_api_doc": False,
                "generate_agents_doc": False,
                "preserve_manual_sections": False,
            },
            "agents": {
                "llm_mode": "api",
                "generation": {
                    "agents_mode": "llm",
                    "readme_mode": "llm",
                    "enable_commit_message": False,
                },
                "api": None,
                "local": None,
                "coding_standards": None,
                "custom_instructions": None,
            },
            "exclude": {
                "directories": [],
                "patterns": [],
            },
            "cache": {
                "enabled": True,
            },
            "debug": {
                "enabled": False,
            },
            "rag": {
                "enabled": True,
                "auto_build_index": False,
                "embedding": {"model": "all-MiniLM-L6-v2", "device": "cpu"},
                "index": {"type": "hnswlib", "ef_construction": 200, "M": 16},
                "retrieval": {"top_k": 6, "score_threshold": 0.3},
                "chunking": {"max_chunk_size": 512, "overlap": 50},
                "exclude_patterns": [
                    r".*\.env$",
                    r"secrets/.*",
                    r".*_SECRET.*",
                    r".*API_KEY.*",
                ],
                "exclude_files": ["README.md", "AGENTS.md"],
            },
        }
        mock_safe_read_toml.return_value = test_config

        mock_safe_read_toml.return_value = test_config

        with patch.object(ConfigManager, "_validate_config"):
            config_manager = ConfigManager(temp_project, docgen_dir, config_path)

            assert config_manager.config == test_config
            mock_safe_read_toml.assert_called_once_with(config_path)

    @patch("docgen.config_manager.safe_read_toml")
    def test_load_config_nonexistent_file(self, mock_safe_read_toml, temp_project):
        """存在しない設定ファイルのテスト"""
        docgen_dir = temp_project / ".docgen"
        docgen_dir.mkdir()
        config_path = docgen_dir / "config.toml"

        mock_safe_read_toml.return_value = None

        with (
            patch.object(
                ConfigManager, "_create_default_config", return_value={"default": "config"}
            ) as mock_default,
            patch.object(ConfigManager, "_validate_config") as mock_validate,
        ):
            config_manager = ConfigManager(temp_project, docgen_dir, config_path)

            assert config_manager.config == {"default": "config"}
            mock_default.assert_called_once()
            mock_validate.assert_called_once()

    @patch("docgen.config_manager.safe_read_toml")
    def test_create_default_config_with_sample(self, mock_safe_read_toml, temp_project):
        """サンプル設定ファイルからのデフォルト設定作成テスト"""
        docgen_dir = temp_project / ".docgen"
        docgen_dir.mkdir()
        sample_path = docgen_dir / "config.toml.sample"
        config_path = docgen_dir / "config.toml"

        # サンプルファイルを作成
        sample_path.write_text("sample: config\n")

        mock_safe_read_toml.side_effect = (
            lambda path: {"sample": "config"} if path == config_path else None
        )

        config_manager = ConfigManager.__new__(ConfigManager)
        config_manager.docgen_dir = docgen_dir
        config_manager.config_path = config_path

        with patch.object(config_manager, "_copy_sample_config", return_value=True):
            result = config_manager._create_default_config()

            assert result == {"sample": "config"}

    @patch("docgen.config_manager.safe_read_toml")
    def test_create_default_config_without_sample(self, mock_safe_read_toml, temp_project):
        """サンプル設定ファイルなしの場合のデフォルト設定作成テスト"""
        docgen_dir = temp_project / ".docgen"
        docgen_dir.mkdir()
        config_path = docgen_dir / "config.toml"

        mock_safe_read_toml.return_value = None

        config_manager = ConfigManager.__new__(ConfigManager)
        config_manager.docgen_dir = docgen_dir
        config_manager.config_path = config_path

        with patch.object(config_manager, "_copy_sample_config", return_value=False):
            with patch.object(
                config_manager, "_get_default_config", return_value={"default": "config"}
            ) as mock_default:
                result = config_manager._create_default_config()

                assert result == {"default": "config"}
                mock_default.assert_called_once()

    def test_copy_sample_config_success(self, temp_project):
        """サンプル設定ファイルのコピー成功テスト"""
        docgen_dir = temp_project / ".docgen"
        docgen_dir.mkdir()
        sample_path = docgen_dir / "config.toml.sample"
        config_path = docgen_dir / "config.toml"

        # サンプルファイルを作成
        sample_content = "sample: content"
        sample_path.write_text(sample_content)

        config_manager = ConfigManager.__new__(ConfigManager)
        config_manager.config_path = config_path

        result = config_manager._copy_sample_config(sample_path)

        assert result is True
        assert config_path.exists()
        assert config_path.read_text() == sample_content

    def test_copy_sample_config_failure(self, temp_project):
        """サンプル設定ファイルのコピー失敗テスト"""
        docgen_dir = temp_project / ".docgen"
        docgen_dir.mkdir()
        sample_path = docgen_dir / "config.toml.sample"
        config_path = docgen_dir / "config.toml"

        # サンプルファイルを作成
        sample_path.write_text("content")

        config_manager = ConfigManager.__new__(ConfigManager)
        config_manager.config_path = config_path

        # shutil.copy2をモックして例外を発生させる
        with patch("shutil.copy2", side_effect=OSError("Copy failed")):
            result = config_manager._copy_sample_config(sample_path)

            assert result is False

    def test_get_default_config(self, temp_project):
        """デフォルト設定の取得テスト"""
        config_manager = ConfigManager.__new__(ConfigManager)

        default_config = config_manager._get_default_config()

        # デフォルト設定に必要なキーが含まれていることを確認
        assert "output" in default_config
        assert "generation" in default_config
        assert "agents" in default_config
        assert "languages" in default_config

        # outputセクションの確認
        assert "agents_doc" in default_config["output"]
        assert "api_doc" in default_config["output"]
        assert "readme" in default_config["output"]

    def test_get_config(self, temp_project):
        """設定取得テスト"""
        docgen_dir = temp_project / ".docgen"
        docgen_dir.mkdir()

        test_config = {
            "languages": {"auto_detect": True, "preferred": []},
            "output": {"api_doc": "docs/api.md", "readme": "README.md", "agents_doc": "AGENTS.md"},
            "generation": {
                "update_readme": True,
                "generate_api_doc": True,
                "generate_agents_doc": True,
                "preserve_manual_sections": True,
            },
            "agents": {
                "llm_mode": "both",
                "generation": {
                    "agents_mode": "template",
                    "readme_mode": "template",
                    "enable_commit_message": True,
                },
                "api": None,
                "local": None,
                "coding_standards": None,
                "custom_instructions": None,
            },
            "exclude": {
                "directories": [],
                "patterns": [],
            },
            "cache": {
                "enabled": True,
            },
            "debug": {
                "enabled": False,
            },
            "rag": {
                "enabled": True,
                "auto_build_index": False,
                "embedding": {"model": "all-MiniLM-L6-v2", "device": "cpu"},
                "index": {"type": "hnswlib", "ef_construction": 200, "M": 16},
                "retrieval": {"top_k": 6, "score_threshold": 0.3},
                "chunking": {"max_chunk_size": 512, "overlap": 50},
                "exclude_patterns": [
                    r".*\.env$",
                    r"secrets/.*",
                    r".*_SECRET.*",
                    r".*API_KEY.*",
                ],
                "exclude_files": ["README.md", "AGENTS.md"],
            },
        }
        with patch.object(ConfigManager, "_load_config", return_value=test_config):
            with patch.object(ConfigManager, "_validate_config"):
                config_manager = ConfigManager(temp_project, docgen_dir)

                result = config_manager.get_config()
                assert result == test_config

    def test_update_config_simple(self, temp_project):
        """シンプルな設定更新テスト"""
        docgen_dir = temp_project / ".docgen"
        docgen_dir.mkdir()

        config_manager = ConfigManager.__new__(ConfigManager)
        config_manager.config = {
            "languages": {"auto_detect": True, "preferred": []},
            "output": {"api_doc": "docs/api.md", "readme": "README.md", "agents_doc": "AGENTS.md"},
            "generation": {
                "update_readme": True,
                "generate_api_doc": True,
                "generate_agents_doc": True,
                "preserve_manual_sections": True,
            },
            "agents": {
                "llm_mode": "both",
                "generation": {
                    "agents_mode": "template",
                    "readme_mode": "template",
                    "enable_commit_message": True,
                },
            },
        }

        with patch.object(config_manager, "_validate_config"):
            config_manager.update_config({"generation.update_readme": False})

            assert config_manager.config["generation"]["update_readme"] is False

    def test_update_config_nested(self, temp_project):
        """ネストされた設定更新テスト"""
        docgen_dir = temp_project / ".docgen"
        docgen_dir.mkdir()

        config_manager = ConfigManager.__new__(ConfigManager)
        config_manager.config = {
            "languages": {"auto_detect": True, "preferred": []},
            "output": {"api_doc": "docs/api.md", "readme": "README.md", "agents_doc": "AGENTS.md"},
            "generation": {
                "update_readme": True,
                "generate_api_doc": True,
                "generate_agents_doc": True,
                "preserve_manual_sections": True,
            },
            "agents": {
                "llm_mode": "both",
                "generation": {
                    "agents_mode": "template",
                    "readme_mode": "template",
                    "enable_commit_message": True,
                },
            },
        }

        with patch.object(config_manager, "_validate_config"):
            config_manager.update_config({"generation.update_readme": False})

            assert config_manager.config["generation"]["update_readme"] is False
