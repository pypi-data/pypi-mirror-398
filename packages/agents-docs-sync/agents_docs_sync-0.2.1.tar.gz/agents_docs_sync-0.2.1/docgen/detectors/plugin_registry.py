"""
カスタムdetectorプラグインのレジストリ
"""

import importlib.util
from pathlib import Path
import sys

from ..utils.logger import get_logger
from .base_detector import BaseDetector

logger = get_logger("plugin_registry")


class PluginRegistry:
    """カスタムdetectorプラグインのレジストリ"""

    def __init__(self):
        """初期化"""
        self._detectors: dict[str, type[BaseDetector]] = {}

    def discover_plugins(self, project_root: Path):
        """
        プロジェクトのプラグインディレクトリからdetectorを発見

        Args:
            project_root: プロジェクトのルートディレクトリ
        """
        plugin_dir = project_root / ".agent" / "detectors"
        if not plugin_dir.exists():
            logger.debug("Plugin directory not found")
            return

        for plugin_file in plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                logger.debug(f"Skipping private plugin: {plugin_file.name}")
                continue

            try:
                self._load_plugin(plugin_file)
            except Exception as e:
                logger.warning(f"Failed to load plugin {plugin_file}: {e}")

    def register(self, detector_class: type[BaseDetector]):
        """
        Detectorクラスを登録

        Args:
            detector_class: BaseDetectorを継承したクラス
        """
        # detector_classにlanguage属性があることを期待
        lang = getattr(detector_class, "language", None)
        if not lang:
            logger.warning(f"Detector class {detector_class.__name__} has no 'language' attribute")
            return

        self._detectors[lang] = detector_class
        logger.info(f"Registered plugin detector: {lang}")

    def get_detector(self, language: str, project_root: Path) -> BaseDetector | None:
        """
        指定された言語のdetectorインスタンスを取得

        Args:
            language: 言語名
            project_root: プロジェクトルート

        Returns:
            Detectorインスタンスまたは None
        """
        detector_class = self._detectors.get(language)
        if detector_class:
            return detector_class(project_root)
        return None

    def get_all_languages(self) -> list[str]:
        """
        登録されている全ての言語名を取得

        Returns:
            言語名のリスト
        """
        return list(self._detectors.keys())

    def _load_plugin(self, plugin_path: Path):
        """
        プラグインファイルを読み込み

        Args:
            plugin_path: プラグインファイルのパス
        """
        module_name = f"custom_detector_{plugin_path.stem}"

        # モジュールの読み込み
        spec = importlib.util.spec_from_file_location(module_name, plugin_path)
        if spec is None or spec.loader is None:
            logger.warning(f"Could not load plugin spec: {plugin_path}")
            return

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # BaseDetectorを継承したクラスを探す
        for attr_name in dir(module):
            if attr_name.startswith("_"):
                continue

            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, BaseDetector) and attr != BaseDetector:
                self.register(attr)
                logger.info(f"Loaded plugin from {plugin_path.name}: {attr_name}")
