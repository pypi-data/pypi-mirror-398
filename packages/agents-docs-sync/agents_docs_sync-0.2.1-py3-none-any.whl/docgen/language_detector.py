"""
言語検出モジュール
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path
from typing import Any

from .detectors.detector_patterns import DetectorPatterns
from .detectors.plugin_registry import PluginRegistry
from .models import DetectedLanguage
from .utils.logger import get_logger

logger = get_logger("language_detector")


class LanguageDetector:
    """言語検出クラス"""

    def __init__(self, project_root: Path, config_manager=None):
        """
        初期化

        Args:
            project_root: プロジェクトルートパス
            config_manager: 設定マネージャー（Noneの場合は新規作成）
        """
        self.project_root = project_root
        self.detected_languages: list[DetectedLanguage] = []
        self.detected_package_managers: dict[str, Any] = {}

        # 設定マネージャーの初期化
        if config_manager:
            self.config_manager = config_manager
        else:
            from .config_manager import ConfigManager

            # docgenディレクトリはプロジェクトルート内のdocgenディレクトリと仮定
            docgen_dir = project_root / "docgen"
            self.config_manager = ConfigManager(project_root, docgen_dir)

        self.plugin_registry = PluginRegistry()

        # 設定の読み込み
        self.configs = self.config_manager.load_detector_defaults()
        user_configs = self.config_manager.load_detector_user_overrides()
        self.configs = self.config_manager.merge_detector_configs(self.configs, user_configs)

        # 設定からexclude.directoriesを取得し、DetectorPatternsに適用
        exclude_directories = self.config_manager.accessor.exclude_directories
        if exclude_directories:
            DetectorPatterns.set_custom_exclude_dirs(exclude_directories)
            logger.debug(f"カスタム除外ディレクトリを設定: {exclude_directories}")

        # 設定からlanguages.ignoredを取得
        self._ignored_languages = set(self.config_manager.accessor.languages_ignored)
        if self._ignored_languages:
            logger.debug(f"無視する言語を設定: {self._ignored_languages}")

        # 設定からlanguages.preferredを取得
        self._preferred_languages = self.config_manager.accessor.languages_preferred
        if self._preferred_languages:
            logger.debug(f"優先する言語を設定: {self._preferred_languages}")

        # プラグインの発見
        self.plugin_registry.discover_plugins(project_root)

        logger.debug(
            f"Config system enabled: {len(self.configs)} configs, "
            f"{len(self.plugin_registry.get_all_languages())} plugins"
        )

    def detect_languages(self, use_parallel: bool = True) -> list[DetectedLanguage]:
        """
        プロジェクトの使用言語を自動検出

        Args:
            use_parallel: 並列処理を使用するかどうか（デフォルト: True）

        Returns:
            検出された言語オブジェクトのリスト
        """
        from .detectors.unified_detector import UnifiedDetectorFactory

        # 統一 detector を使用
        detectors = UnifiedDetectorFactory.create_all_detectors(self.project_root)

        # プラグインdetectorを追加（優先度が高い）
        for lang in self.plugin_registry.get_all_languages():
            plugin_detector = self.plugin_registry.get_detector(lang, self.project_root)
            if plugin_detector:
                detectors.insert(0, plugin_detector)  # type: ignore[arg-type]

        detected: list[DetectedLanguage] = []
        package_managers = {}

        if use_parallel:
            # 並列処理で検出（スレッド数はCPU数に基づいて制限）
            # 過剰なスレッドはI/O競合を引き起こす可能性があるため
            max_workers = min(len(detectors), (os.cpu_count() or 4) * 2)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_detector = {
                    executor.submit(detector.detect): detector for detector in detectors
                }

                for future in as_completed(future_to_detector):
                    detector = future_to_detector[future]
                    try:
                        if future.result():
                            # UnifiedDetectorならオブジェクト取得可能
                            if hasattr(detector, "get_detected_language_object"):
                                lang_obj = detector.get_detected_language_object()
                            else:
                                # プラグイン等のフォールバック
                                lang_name = detector.get_language()
                                pm = detector.detect_package_manager()
                                lang_obj = DetectedLanguage(
                                    name=lang_name,
                                    package_manager=pm,
                                    source_extensions=DetectorPatterns.get_source_extensions(
                                        lang_name
                                    ),
                                )

                            # 名前で重複チェック
                            if not any(lang.name == lang_obj.name for lang in detected):
                                detected.append(lang_obj)
                                logger.info(f"✓ 検出: {lang_obj.name}")

                                # パッケージマネージャ情報の更新（後方互換性のため）
                                if lang_obj.package_manager:
                                    package_managers[lang_obj.name] = lang_obj.package_manager
                                    logger.info(
                                        f"✓ パッケージマネージャ検出: {lang_obj.name} -> {lang_obj.package_manager}"
                                    )
                    except Exception as e:
                        logger.warning(
                            f"言語検出中にエラーが発生しました ({detector.__class__.__name__}): {e}"
                        )
        else:
            # 逐次処理で検出
            for detector in detectors:
                try:
                    if detector.detect():
                        # UnifiedDetectorならオブジェクト取得可能
                        if hasattr(detector, "get_detected_language_object"):
                            lang_obj = detector.get_detected_language_object()
                        else:
                            # プラグイン等のフォールバック
                            lang_name = detector.get_language()
                            pm = detector.detect_package_manager()
                            lang_obj = DetectedLanguage(
                                name=lang_name,
                                package_manager=pm,
                                source_extensions=DetectorPatterns.get_source_extensions(lang_name),
                            )

                        # 名前で重複チェック
                        if not any(lang.name == lang_obj.name for lang in detected):
                            detected.append(lang_obj)
                            logger.info(f"✓ 検出: {lang_obj.name}")

                            # パッケージマネージャ情報の更新（後方互換性のため）
                            if lang_obj.package_manager:
                                package_managers[lang_obj.name] = lang_obj.package_manager
                                logger.info(
                                    f"✓ パッケージマネージャ検出: {lang_obj.name} -> {lang_obj.package_manager}"
                                )
                except Exception as e:
                    logger.warning(
                        f"言語検出中にエラーが発生しました ({detector.__class__.__name__}): {e}"
                    )

        # languages.ignoredで指定された言語をフィルタリング
        if self._ignored_languages:
            ignored_count = 0
            for lang_obj in list(detected):
                if lang_obj.name in self._ignored_languages:
                    detected.remove(lang_obj)
                    if lang_obj.name in package_managers:
                        del package_managers[lang_obj.name]
                    ignored_count += 1
                    logger.info(f"× 無視: {lang_obj.name} (languages.ignoredで設定)")
            if ignored_count > 0:
                logger.debug(f"{ignored_count}個の言語を無視しました")

        # languages.preferredで指定された言語を優先順位に基づいて並び替え
        if self._preferred_languages:
            # preferredリストの順序に基づいてソート
            # preferredに含まれる言語を先頭に、含まれない言語を後ろに配置
            def sort_key(lang_obj: DetectedLanguage) -> tuple[int, str]:
                try:
                    # preferredリスト内のインデックスを取得（小さいほど優先）
                    index = self._preferred_languages.index(lang_obj.name)
                    return (0, str(index))  # preferredに含まれる場合は(0, index)
                except ValueError:
                    return (1, lang_obj.name)  # preferredに含まれない場合は(1, name)

            detected.sort(key=sort_key)
            logger.debug(
                f"言語を優先順位に基づいて並び替えました: {[lang.name for lang in detected]}"
            )

        self.detected_languages = detected
        self.detected_package_managers = package_managers

        # 検出完了後、キャッシュをクリア（メモリリーク防止）
        # ただし、同じプロジェクトで再度検出する可能性があるため、クリアは任意
        # DetectorPatterns.clear_cache(self.project_root)

        return detected

    def get_detected_languages(self) -> list[str]:
        """検出された言語名のリストを取得（後方互換性用）"""
        return [lang.name for lang in self.detected_languages]

    def get_detected_language_objects(self) -> list[DetectedLanguage]:
        """検出された言語オブジェクトのリストを取得"""
        return self.detected_languages

    def get_detected_package_managers(self) -> dict[str, str]:
        """検出されたパッケージマネージャを取得"""
        return self.detected_package_managers
