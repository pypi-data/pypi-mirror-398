# API ドキュメント

自動生成日時: 2025-12-24 16:04:06

---

## docgen/archgen/detectors/python_detector.py

### PythonDetector

**型**: `class`

**シグネチャ**:
```
class PythonDetector:
```

**説明**:

Python プロジェクトを検出

*定義場所: docgen/archgen/detectors/python_detector.py:11*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, exclude_directories: list[str] | None, exclude_patterns: set[str] | None):
```

**説明**:

初期化

Args:
    exclude_directories: 除外するディレクトリのリスト
    exclude_patterns: 依存関係から除外するパターンのセット

*定義場所: docgen/archgen/detectors/python_detector.py:17*

---

### detect

**型**: `method`

**シグネチャ**:
```
def detect(self, project_root: Path) -> list[Service]:
```

*説明なし*

*定義場所: docgen/archgen/detectors/python_detector.py:34*

---


## docgen/archgen/generators/mermaid_generator.py

### MermaidGenerator

**型**: `class`

**シグネチャ**:
```
class MermaidGenerator:
```

**説明**:

Mermaid.js形式でアーキテクチャ図を生成（依存なし）

*定義場所: docgen/archgen/generators/mermaid_generator.py:11*

---

### generate

**型**: `method`

**シグネチャ**:
```
def generate(self, manifest: ArchitectureManifest, output_dir: Path) -> Path:
```

**説明**:

Mermaid形式のアーキテクチャ図を生成

*定義場所: docgen/archgen/generators/mermaid_generator.py:23*

---


## docgen/archgen/scanner.py

### ProjectScanner

**型**: `class`

**シグネチャ**:
```
class ProjectScanner:
```

**説明**:

プロジェクトをスキャンしてアーキテクチャを抽出

*定義場所: docgen/archgen/scanner.py:14*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, project_root: Path, exclude_directories: list[str] | None, config: dict[str, Any] | None):
```

**説明**:

初期化

Args:
    project_root: プロジェクトルートディレクトリ
    exclude_directories: 除外するディレクトリのリスト
    config: 設定辞書（依存関係フィルタリング用）

*定義場所: docgen/archgen/scanner.py:17*

---

### scan

**型**: `method`

**シグネチャ**:
```
def scan(self) -> ArchitectureManifest:
```

**説明**:

プロジェクトをスキャン

Returns:
    アーキテクチャマニフェスト（サービス重複除去済み）

*定義場所: docgen/archgen/scanner.py:100*

---


## docgen/benchmark/comparator.py

### BenchmarkComparator

**型**: `class`

**シグネチャ**:
```
class BenchmarkComparator:
```

**説明**:

ベンチマーク結果の比較クラス

*定義場所: docgen/benchmark/comparator.py:13*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, baseline_path: Path, current_path: Path):
```

**説明**:

初期化

Args:
    baseline_path: ベースライン（比較元）のJSONファイルパス
    current_path: 現在の（比較先）のJSONファイルパス

*定義場所: docgen/benchmark/comparator.py:16*

---

### compare

**型**: `method`

**シグネチャ**:
```
def compare(self) -> dict[str, Any]:
```

**説明**:

ベンチマーク結果を比較

Returns:
    比較結果の辞書

*定義場所: docgen/benchmark/comparator.py:45*

---

### generate_comparison_report

**型**: `method`

**シグネチャ**:
```
def generate_comparison_report(self) -> str:
```

**説明**:

比較レポートをMarkdown形式で生成

Returns:
    Markdown形式のレポート

*定義場所: docgen/benchmark/comparator.py:162*

---

### save_comparison_report

**型**: `method`

**シグネチャ**:
```
def save_comparison_report(self, path: Path) -> None:
```

**説明**:

比較レポートをファイルに保存

Args:
    path: 保存先のパス

*定義場所: docgen/benchmark/comparator.py:255*

---


## docgen/benchmark/reporter.py

### BenchmarkReporter

**型**: `class`

**シグネチャ**:
```
class BenchmarkReporter:
```

**説明**:

ベンチマーク結果のレポート生成クラス

*定義場所: docgen/benchmark/reporter.py:16*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, recorder: BenchmarkRecorder | None):
```

**説明**:

初期化

Args:
    recorder: ベンチマークレコーダー（Noneの場合はグローバルレコーダーを使用）

*定義場所: docgen/benchmark/reporter.py:19*

---

### generate_markdown

**型**: `method`

**シグネチャ**:
```
def generate_markdown(self, include_children: bool) -> str:
```

**説明**:

Markdown形式のレポートを生成

Args:
    include_children: 子処理の結果を含めるかどうか

Returns:
    Markdown形式のレポート

*定義場所: docgen/benchmark/reporter.py:28*

---

### generate_json

**型**: `method`

**シグネチャ**:
```
def generate_json(self) -> dict[str, Any]:
```

**説明**:

JSON形式のレポートを生成

Returns:
    JSON形式の辞書

*定義場所: docgen/benchmark/reporter.py:112*

---

### save_markdown

**型**: `method`

**シグネチャ**:
```
def save_markdown(self, path: Path) -> None:
```

**説明**:

Markdownレポートをファイルに保存

Args:
    path: 保存先のパス

*定義場所: docgen/benchmark/reporter.py:121*

---

### save_json

**型**: `method`

**シグネチャ**:
```
def save_json(self, path: Path) -> None:
```

**説明**:

JSONレポートをファイルに保存

Args:
    path: 保存先のパス

*定義場所: docgen/benchmark/reporter.py:131*

---

### generate_csv

**型**: `method`

**シグネチャ**:
```
def generate_csv(self, include_children: bool) -> str:
```

**説明**:

CSV形式のレポートを生成

Args:
    include_children: 子処理の結果を含めるかどうか

Returns:
    CSV形式の文字列

*定義場所: docgen/benchmark/reporter.py:141*

---

### save_csv

**型**: `method`

**シグネチャ**:
```
def save_csv(self, path: Path, include_children: bool) -> None:
```

**説明**:

CSVレポートをファイルに保存

Args:
    path: 保存先のパス
    include_children: 子処理の結果を含めるかどうか

*定義場所: docgen/benchmark/reporter.py:210*

---

### detect_bottlenecks

**型**: `method`

**シグネチャ**:
```
def detect_bottlenecks(self, threshold_percent: float) -> list[str]:
```

**説明**:

ボトルネックを検出

Args:
    threshold_percent: ボトルネックとみなす実行時間の割合（%）

Returns:
    ボトルネックの処理名のリスト

*定義場所: docgen/benchmark/reporter.py:221*

---


## docgen/benchmark/utils.py

### get_current_process

**型**: `function`

**シグネチャ**:
```
def get_current_process() -> psutil.Process:
```

**説明**:

現在のプロセスを取得

Returns:
    現在のプロセス

*定義場所: docgen/benchmark/utils.py:10*

---

### format_duration

**型**: `function`

**シグネチャ**:
```
def format_duration(seconds: float) -> str:
```

**説明**:

実行時間をフォーマット

Args:
    seconds: 秒数

Returns:
    フォーマットされた文字列

*定義場所: docgen/benchmark/utils.py:20*

---

### format_memory

**型**: `function`

**シグネチャ**:
```
def format_memory(bytes_size: int) -> str:
```

**説明**:

メモリサイズをフォーマット

Args:
    bytes_size: バイト数

Returns:
    フォーマットされた文字列

*定義場所: docgen/benchmark/utils.py:38*

---


## docgen/cli/commands/hooks.py

### HooksCommand

**型**: `class`

**シグネチャ**:
```
class HooksCommand:
```

**説明**:

Git hooks管理コマンド

*定義場所: docgen/cli/commands/hooks.py:17*

---

### execute

**型**: `method`

**シグネチャ**:
```
def execute(self, args: Namespace, project_root: Path) -> int:
```

**説明**:

Handle Git hooks management actions

Args:
    args: Command line arguments
    project_root: Project root directory

Returns:
    Exit code (0 for success, 1 for failure)

*定義場所: docgen/cli/commands/hooks.py:20*

---


## docgen/cli/runner.py

### CommandRunner

**型**: `class`

**シグネチャ**:
```
class CommandRunner:
```

**説明**:

コマンド実行を管理するオーケストレーター

*定義場所: docgen/cli/runner.py:21*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self):
```

*説明なし*

*定義場所: docgen/cli/runner.py:24*

---

### run

**型**: `method`

**シグネチャ**:
```
def run(self, args: Namespace, project_root: Path) -> int:
```

**説明**:

Execute the appropriate command based on parsed arguments

Args:
    args: Parsed command line arguments
    project_root: Project root directory

Returns:
    Exit code (0 for success, 1 for failure)

*定義場所: docgen/cli/runner.py:36*

---


## docgen/collectors/coding_standards_collector.py

### CodingStandardsCollector

**型**: `class`

**シグネチャ**:
```
class CodingStandardsCollector:
```

**説明**:

Coding standards collector class

*定義場所: docgen/collectors/coding_standards_collector.py:12*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, project_root: Path, logger: Any | None):
```

**説明**:

Initialize

Args:
    project_root: Project root directory
    logger: Logger instance

*定義場所: docgen/collectors/coding_standards_collector.py:19*

---

### collect_coding_standards

**型**: `method`

**シグネチャ**:
```
def collect_coding_standards(self) -> dict[str, str | dict[str, Any] | bool]:
```

**説明**:

Collect coding standards

Returns:
    Dictionary of coding standards

*定義場所: docgen/collectors/coding_standards_collector.py:30*

---


## docgen/collectors/command_help_extractor.py

### CommandHelpExtractor

**型**: `class`

**シグネチャ**:
```
class CommandHelpExtractor:
```

**説明**:

Extract help text from Python CLI entry points

*定義場所: docgen/collectors/command_help_extractor.py:17*

---

### extract_from_entry_point

**型**: `method`

**シグネチャ**:
```
def extract_from_entry_point(entry_point: str, project_root: Path | None) -> str:
```

**説明**:

Extract description from a Python entry point

Args:
    entry_point: Entry point string in format "module.path:function"
    project_root: Project root directory to add to sys.path

Returns:
    Description string, or empty string if extraction fails

*定義場所: docgen/collectors/command_help_extractor.py:86*

---

### extract_options_from_entry_point

**型**: `method`

**シグネチャ**:
```
def extract_options_from_entry_point(entry_point: str, project_root: Path | None) -> list[dict[str, str]]:
```

**説明**:

Extract command options from a Python entry point

Args:
    entry_point: Entry point string in format "module.path:function"
    project_root: Project root directory to add to sys.path

Returns:
    List of option dicts with 'name' and 'help' keys

*定義場所: docgen/collectors/command_help_extractor.py:173*

---

### extract_structured_commands_from_entry_point

**型**: `method`

**シグネチャ**:
```
def extract_structured_commands_from_entry_point(entry_point: str, project_root: Path | None) -> dict[str, Any]:
```

**説明**:

Extract structured command hierarchy from a Python entry point.

Returns a structured dict with:
- options: list of main CLI options (e.g., --config, --detect-only)
- subcommands: dict of subcommand name -> {help, options, subcommands}

Args:
    entry_point: Entry point string in format "module.path:function"
    project_root: Project root directory to add to sys.path

Returns:
    Structured command hierarchy dict

*定義場所: docgen/collectors/command_help_extractor.py:280*

---


## docgen/collectors/language_info_collector.py

### LanguageInfoCollector

**型**: `class`

**シグネチャ**:
```
class LanguageInfoCollector:
```

**説明**:

言語固有情報収集クラス

*定義場所: docgen/collectors/language_info_collector.py:13*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, project_root: Path, logger: Any | None):
```

*説明なし*

*定義場所: docgen/collectors/language_info_collector.py:24*

---

### collect

**型**: `method`

**シグネチャ**:
```
def collect(self) -> dict[str, Any]:
```

**説明**:

言語固有情報を収集

Returns:
    収集した情報の辞書

*定義場所: docgen/collectors/language_info_collector.py:27*

---

### collect_scripts

**型**: `method`

**シグネチャ**:
```
def collect_scripts(self) -> dict[str, dict[str, str]]:
```

**説明**:

実行可能なスクリプトを収集

Returns:
    スクリプト名と詳細情報の辞書 {name: {command: str, description: str}}

*定義場所: docgen/collectors/language_info_collector.py:39*

---

### collect_project_description

**型**: `method`

**シグネチャ**:
```
def collect_project_description(self) -> str | None:
```

**説明**:

プロジェクトの説明を収集

優先順位:
1. package.json (JavaScript/TypeScript プロジェクト)
2. pyproject.toml (Python プロジェクト)
3. setup.py (古いPythonプロジェクト)
4. README.md (上記が存在しない場合のみ)

Returns:
    プロジェクトの説明文（見つからない場合はNone）

*定義場所: docgen/collectors/language_info_collector.py:141*

---


## docgen/collectors/structure_analyzer.py

### StructureAnalyzer

**型**: `class`

**シグネチャ**:
```
class StructureAnalyzer:
```

**説明**:

プロジェクト構造分析クラス

*定義場所: docgen/collectors/structure_analyzer.py:15*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, project_root: Path, logger: Any | None, exclude_directories: list[str] | None):
```

**説明**:

初期化

Args:
    project_root: プロジェクトのルートディレクトリ
    logger: ロガーインスタンス
    exclude_directories: 除外するディレクトリのリスト（追加分）

*定義場所: docgen/collectors/structure_analyzer.py:51*

---

### collect

**型**: `method`

**シグネチャ**:
```
def collect(self, max_depth: int) -> dict[str, Any]:
```

**説明**:

プロジェクト構造を収集（BaseCollectorインターフェース実装）

Args:
    max_depth: ディレクトリの最大探索深度

Returns:
    プロジェクト構造の辞書

*定義場所: docgen/collectors/structure_analyzer.py:71*

---

### count_symbols_in_file

**型**: `method`

**シグネチャ**:
```
def count_symbols_in_file(self, file_path: Path) -> int:
```

**説明**:

Pythonファイルのシンボル数をカウント

Args:
    file_path: Pythonファイルのパス

Returns:
    シンボル数（クラス、関数、非同期関数の合計）

*定義場所: docgen/collectors/structure_analyzer.py:83*

---

### collect_directory_structure

**型**: `method`

**シグネチャ**:
```
def collect_directory_structure(self, directory: Path, max_depth: int, current_depth: int) -> dict[str, Any] | str:
```

**説明**:

ディレクトリ構造を再帰的に収集

Args:
    directory: 対象ディレクトリ
    max_depth: 最大探索深度
    current_depth: 現在の深度

Returns:
    ディレクトリ構造の辞書、またはネストしないディレクトリの場合は "directory"

*定義場所: docgen/collectors/structure_analyzer.py:106*

---

### analyze

**型**: `method`

**シグネチャ**:
```
def analyze(self, max_depth: int) -> dict[str, Any]:
```

**説明**:

プロジェクト構造を分析

Args:
    max_depth: ディレクトリの最大探索深度

Returns:
    プロジェクト構造の辞書

*定義場所: docgen/collectors/structure_analyzer.py:168*

---


## docgen/detector_config_loader.py

### DetectorConfigLoader

**型**: `class`

**シグネチャ**:
```
class DetectorConfigLoader:
```

**説明**:

Loader for detector configurations

*定義場所: docgen/detector_config_loader.py:13*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, project_root: Path):
```

*説明なし*

*定義場所: docgen/detector_config_loader.py:16*

---

### load_defaults

**型**: `method`

**シグネチャ**:
```
def load_defaults(self) -> dict[str, Any]:
```

**説明**:

Load default detector configurations

Returns:
    Dictionary of language configurations

*定義場所: docgen/detector_config_loader.py:19*

---

### load_user_overrides

**型**: `method`

**シグネチャ**:
```
def load_user_overrides(self) -> dict[str, Any]:
```

**説明**:

Load detector configuration from config.toml

Returns:
    Detector configuration dictionary

*定義場所: docgen/detector_config_loader.py:48*

---

### merge_configs

**型**: `method`

**シグネチャ**:
```
def merge_configs(self, defaults: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
```

**説明**:

Merge default and user configurations

Args:
    defaults: Default configurations
    overrides: User configurations

Returns:
    Merged configurations

*定義場所: docgen/detector_config_loader.py:76*

---


## docgen/detectors/detector_patterns.py

### DetectorPatterns

**型**: `class`

**シグネチャ**:
```
class DetectorPatterns:
```

**説明**:

Common file detection patterns used by language detectors.

*定義場所: docgen/detectors/detector_patterns.py:8*

---

### get_package_files

**型**: `method`

**シグネチャ**:
```
def get_package_files(cls, language: str) -> list[str]:
```

**説明**:

Get package manager files for a language.

*定義場所: docgen/detectors/detector_patterns.py:196*

---

### get_source_extensions

**型**: `method`

**シグネチャ**:
```
def get_source_extensions(cls, language: str) -> list[str]:
```

**説明**:

Get source file extensions for a language.

*定義場所: docgen/detectors/detector_patterns.py:201*

---

### detect_by_package_files

**型**: `method`

**シグネチャ**:
```
def detect_by_package_files(cls, project_root: Path, language: str) -> bool:
```

**説明**:

Detect language by checking for package manager files.

*定義場所: docgen/detectors/detector_patterns.py:206*

---

### detect_by_source_files

**型**: `method`

**シグネチャ**:
```
def detect_by_source_files(cls, project_root: Path, language: str) -> bool:
```

**説明**:

Detect language by checking for source files.

*定義場所: docgen/detectors/detector_patterns.py:212*

---

### detect_by_source_files_with_exclusions

**型**: `method`

**シグネチャ**:
```
def detect_by_source_files_with_exclusions(cls, project_root: Path, language: str) -> bool:
```

**説明**:

Detect language by checking for source files, excluding common directories.

*定義場所: docgen/detectors/detector_patterns.py:224*

---

### detect_by_extensions_with_exclusions

**型**: `method`

**シグネチャ**:
```
def detect_by_extensions_with_exclusions(cls, project_root: Path, extensions: list[str], max_file_size: int) -> bool:
```

**説明**:

Detect files by extensions, excluding common directories.

Args:
    project_root: プロジェクトルートディレクトリ
    extensions: 検索する拡張子のリスト
    max_file_size: スキップする最大ファイルサイズ（バイト、デフォルト: 10MB）
                  大きなファイルは検出対象外として扱う

*定義場所: docgen/detectors/detector_patterns.py:300*

---

### is_excluded_path

**型**: `method`

**シグネチャ**:
```
def is_excluded_path(cls, path: Path, project_root: Path) -> bool:
```

**説明**:

Check if a path should be excluded from detection.

*定義場所: docgen/detectors/detector_patterns.py:348*

---

### detect_package_manager

**型**: `method`

**シグネチャ**:
```
def detect_package_manager(cls, language: str, file_exists_func) -> str | None:
```

**説明**:

Detect package manager for a language using file existence checks.

Args:
    language: Language name
    file_exists_func: Function that takes file patterns (str or tuple) and returns bool

Returns:
    Package manager name or None

*定義場所: docgen/detectors/detector_patterns.py:358*

---

### is_js_config_or_test

**型**: `method`

**シグネチャ**:
```
def is_js_config_or_test(cls, file_path: Path) -> bool:
```

**説明**:

Check if a file is likely a JavaScript config or test file.

*定義場所: docgen/detectors/detector_patterns.py:381*

---

### clear_cache

**型**: `method`

**シグネチャ**:
```
def clear_cache(cls, project_root: Path | None) -> None:
```

**説明**:

Clear file detection cache.

Args:
    project_root: If provided, clear cache for this project only.
                 If None, clear all caches.

*定義場所: docgen/detectors/detector_patterns.py:387*

---

### set_custom_exclude_dirs

**型**: `method`

**シグネチャ**:
```
def set_custom_exclude_dirs(cls, directories: list[str]) -> None:
```

**説明**:

設定ファイルからのカスタム除外ディレクトリを設定.

Args:
    directories: 除外するディレクトリ名のリスト

*定義場所: docgen/detectors/detector_patterns.py:405*

---

### get_all_exclude_dirs

**型**: `method`

**シグネチャ**:
```
def get_all_exclude_dirs(cls) -> set[str]:
```

**説明**:

デフォルトとカスタムの除外ディレクトリをマージして取得.

Returns:
    除外ディレクトリのセット

*定義場所: docgen/detectors/detector_patterns.py:417*

---

### detect_python_package_manager

**型**: `method`

**シグネチャ**:
```
def detect_python_package_manager(cls, project_root: Path) -> str | None:
```

**説明**:

Detect Python package manager with special handling for pyproject.toml.

*定義場所: docgen/detectors/detector_patterns.py:426*

---


## docgen/detectors/unified_detector.py

### UnifiedDetector

**型**: `class`

**シグネチャ**:
```
class UnifiedDetector:
```

**説明**:

パターンベースの統一言語検出クラス

DetectorPatterns で定義されたすべての言語を検出します。

*定義場所: docgen/detectors/unified_detector.py:16*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, project_root: Path, language: str):
```

**説明**:

初期化

Args:
    project_root: プロジェクトのルートディレクトリ
    language: 検出対象の言語名

*定義場所: docgen/detectors/unified_detector.py:22*

---

### detect

**型**: `method`

**シグネチャ**:
```
def detect(self) -> bool:
```

**説明**:

指定された言語が使用されているか検出

Returns:
    検出された場合True

*定義場所: docgen/detectors/unified_detector.py:34*

---

### get_language

**型**: `method`

**シグネチャ**:
```
def get_language(self) -> str:
```

**説明**:

検出された言語名を返す

Returns:
    言語名（例: 'python', 'javascript'）

*定義場所: docgen/detectors/unified_detector.py:57*

---

### detect_package_manager

**型**: `method`

**シグネチャ**:
```
def detect_package_manager(self) -> str | None:
```

**説明**:

使用されているパッケージマネージャを検出

Returns:
    パッケージマネージャ名（例: 'pip', 'npm', 'yarn'）またはNone

*定義場所: docgen/detectors/unified_detector.py:66*

---

### get_detected_language_object

**型**: `method`

**シグネチャ**:
```
def get_detected_language_object(self) -> DetectedLanguage:
```

**説明**:

検出された言語のオブジェクトを返す

Returns:
    DetectedLanguage オブジェクト

*定義場所: docgen/detectors/unified_detector.py:88*

---

### UnifiedDetectorFactory

**型**: `class`

**シグネチャ**:
```
class UnifiedDetectorFactory:
```

**説明**:

UnifiedDetector のファクトリークラス

サポートされているすべての言語の detector を生成します。

*定義場所: docgen/detectors/unified_detector.py:104*

---

### get_all_languages

**型**: `method`

**シグネチャ**:
```
def get_all_languages(cls) -> list[str]:
```

**説明**:

サポートされているすべての言語を取得

Returns:
    言語名のリスト（よく使われる言語を優先）

*定義場所: docgen/detectors/unified_detector.py:111*

---

### create_detector

**型**: `method`

**シグネチャ**:
```
def create_detector(cls, project_root: Path, language: str) -> UnifiedDetector:
```

**説明**:

指定された言語の detector を作成

Args:
    project_root: プロジェクトのルートディレクトリ
    language: 言語名

Returns:
    UnifiedDetector インスタンス

*定義場所: docgen/detectors/unified_detector.py:137*

---

### create_all_detectors

**型**: `method`

**シグネチャ**:
```
def create_all_detectors(cls, project_root: Path) -> list[UnifiedDetector]:
```

**説明**:

すべての言語の detector を作成

Args:
    project_root: プロジェクトのルートディレクトリ

Returns:
    UnifiedDetector インスタンスのリスト

*定義場所: docgen/detectors/unified_detector.py:151*

---


## docgen/docgen.py

### DocGen

**型**: `class`

**シグネチャ**:
```
class DocGen:
```

**説明**:

ドキュメント自動生成メインクラス

*定義場所: docgen/docgen.py:28*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, project_root: Path | None, config_path: Path | None):
```

**説明**:

初期化

Args:
    project_root: プロジェクトのルートディレクトリ（Noneの場合は現在の作業ディレクトリ）
    config_path: 設定ファイルのパス（Noneの場合はデフォルト）

*定義場所: docgen/docgen.py:31*

---

### detect_languages

**型**: `method`

**シグネチャ**:
```
def detect_languages(self, use_parallel: bool) -> list[DetectedLanguage]:
```

**説明**:

プロジェクトの使用言語を自動検出

Args:
    use_parallel: 並列処理を使用するかどうか（デフォルト: True）

Returns:
    検出された言語オブジェクトのリスト

*定義場所: docgen/docgen.py:66*

---

### update_config

**型**: `method`

**シグネチャ**:
```
def update_config(self, updates: dict[str, Any]) -> None:
```

**説明**:

設定を動的に更新

Args:
    updates: 更新する設定辞書（ドット記法対応、例: {'generation.update_readme': False}）

*定義場所: docgen/docgen.py:82*

---

### generate_documents

**型**: `method`

**シグネチャ**:
```
def generate_documents(self) -> bool:
```

**説明**:

ドキュメントを生成

Returns:
    成功したかどうか

*定義場所: docgen/docgen.py:92*

---

### run_cli

**型**: `function`

**シグネチャ**:
```
def run_cli() -> int:
```

**説明**:

Run the command line interface

Returns:
    Exit code

*定義場所: docgen/docgen.py:148*

---

### main

**型**: `function`

**シグネチャ**:
```
def main():
```

**説明**:

メインエントリーポイント

*定義場所: docgen/docgen.py:173*

---


## docgen/generator_factory.py

### GeneratorFactory

**型**: `class`

**シグネチャ**:
```
class GeneratorFactory:
```

**説明**:

ジェネレーターのファクトリークラス

*定義場所: docgen/generator_factory.py:12*

---

### create_generator

**型**: `method`

**シグネチャ**:
```
def create_generator(cls, generator_type: str, project_root: Path, detected_languages: list[str], config: dict[str, Any], detected_package_managers: dict[str, str] | None) -> BaseGenerator:
```

**説明**:

指定されたタイプのジェネレーターを作成

*定義場所: docgen/generator_factory.py:24*

---

### get_available_generators

**型**: `method`

**シグネチャ**:
```
def get_available_generators(cls) -> list[str]:
```

**説明**:

利用可能なジェネレーターのリストを取得

*定義場所: docgen/generator_factory.py:53*

---


## docgen/generators/agents_generator.py

### AgentsGenerator

**型**: `class`

**シグネチャ**:
```
class AgentsGenerator:
```

**説明**:

AGENTS.md生成クラス（OpenAI仕様準拠）

*定義場所: docgen/generators/agents_generator.py:22*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, project_root: Path, languages: list[str], config: dict[str, Any], package_managers: dict[str, str] | None):
```

**説明**:

初期化

Args:
    project_root: プロジェクトのルートディレクトリ
    languages: 検出された言語のリスト
    config: 設定辞書
    package_managers: 検出されたパッケージマネージャの辞書
    **kwargs: BaseGeneratorに渡す追加引数（サービスなど）

*定義場所: docgen/generators/agents_generator.py:25*

---

### agents_path

**型**: `method`

**シグネチャ**:
```
def agents_path(self):
```

*説明なし*

*定義場所: docgen/generators/agents_generator.py:49*

---


## docgen/generators/api_generator.py

### APIGenerator

**型**: `class`

**シグネチャ**:
```
class APIGenerator:
```

**説明**:

APIドキュメント生成クラス

*定義場所: docgen/generators/api_generator.py:25*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, project_root: Path, languages: list[str], config: dict[str, Any], package_managers: dict[str, str] | None):
```

**説明**:

初期化

Args:
    project_root: プロジェクトのルートディレクトリ
    languages: 検出された言語のリスト
    config: 設定辞書
    package_managers: 検出されたパッケージマネージャの辞書

*定義場所: docgen/generators/api_generator.py:28*

---


## docgen/generators/base_generator.py

### BaseGenerator

**型**: `class`

**シグネチャ**:
```
class BaseGenerator:
```

**説明**:

ベースジェネレータークラス（AGENTS.mdとREADME.mdの共通部分）

DI対応: コンストラクタでサービスを注入可能。

*定義場所: docgen/generators/base_generator.py:24*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, project_root: Path, languages: list[str], config: dict[str, Any], package_managers: dict[str, str] | None):
```

**説明**:

初期化

Args:
    project_root: プロジェクトのルートディレクトリ
    languages: 検出された言語のリスト
    config: 設定辞書
    package_managers: 検出されたパッケージマネージャの辞書
    llm_service: LLMサービス（DI）
    template_service: テンプレートサービス（DI）
    rag_service: RAGサービス（DI）
    formatting_service: フォーマットサービス（DI）
    manual_section_service: 手動セクションサービス（DI）

*定義場所: docgen/generators/base_generator.py:30*

---

### generate

**型**: `method`

**シグネチャ**:
```
def generate(self) -> bool:
```

**説明**:

ドキュメントを生成

Returns:
    生成に成功した場合True

*定義場所: docgen/generators/base_generator.py:221*

---


## docgen/generators/contributing_generator.py

### ContributingGenerator

**型**: `class`

**シグネチャ**:
```
class ContributingGenerator:
```

**説明**:

CONTRIBUTING.md generation class

*定義場所: docgen/generators/contributing_generator.py:12*

---


## docgen/generators/parsers/base_parser.py

### BaseParser

**型**: `class`

**シグネチャ**:
```
class BaseParser:
```

**説明**:

コード解析のベースクラス

Template Methodパターンにより、解析フローの共通部分を定義します。
サブクラスでは以下の抽象メソッドを実装します：
- `_parse_to_ast`: コンテンツをASTにパース
- `_extract_elements`: ASTからAPI要素を抽出
- `get_supported_extensions`: サポートする拡張子を返す

Attributes:
    PARSER_TYPE: パーサーの種類を示すクラス変数

*定義場所: docgen/generators/parsers/base_parser.py:25*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, project_root: Path):
```

**説明**:

初期化

Args:
    project_root: プロジェクトのルートディレクトリ

*定義場所: docgen/generators/parsers/base_parser.py:40*

---

### parse_file

**型**: `method`

**シグネチャ**:
```
def parse_file(self, file_path: Path) -> list[APIInfo]:
```

**説明**:

ファイルを解析してAPI情報を抽出 (Template Method)

Args:
    file_path: 解析するファイルのパス

Returns:
    API情報のリスト

*定義場所: docgen/generators/parsers/base_parser.py:49*

---

### get_supported_extensions

**型**: `method`

**シグネチャ**:
```
def get_supported_extensions(self) -> list[str]:
```

**説明**:

サポートするファイル拡張子を返す

Returns:
    拡張子のリスト（例: ['.py', '.pyw']）

*定義場所: docgen/generators/parsers/base_parser.py:94*

---

### get_parser_type

**型**: `method`

**シグネチャ**:
```
def get_parser_type(self) -> str:
```

**説明**:

パーサーの種類を返す（キャッシュキーの生成に使用）

Returns:
    パーサーの種類（例: 'python', 'javascript'）

*定義場所: docgen/generators/parsers/base_parser.py:103*

---

### parse_project

**型**: `method`

**シグネチャ**:
```
def parse_project(self, exclude_dirs: list[str] | None, use_parallel: bool, max_workers: int | None, use_cache: bool, cache_manager: 'CacheManager | None', files_to_parse: list[tuple[Path, Path]] | None, skip_cache_save: bool, gitignore_matcher: 'GitIgnoreMatcher | None') -> list[APIInfo]:
```

**説明**:

プロジェクト全体を解析

Args:
    exclude_dirs: 除外するディレクトリ（例: ['.git', 'node_modules']）
    use_parallel: 並列処理を使用するかどうか（デフォルト: True）
    max_workers: 並列処理の最大ワーカー数（Noneの場合は自動）
    use_cache: キャッシュを使用するかどうか（デフォルト: True）
    cache_manager: キャッシュマネージャー（Noneの場合はキャッシュを使用しない）
    files_to_parse: 既にスキャン済みのファイルリスト（Noneの場合は新規スキャン）
    skip_cache_save: キャッシュ保存をスキップするか（デフォルト: False）
    gitignore_matcher: .gitignoreマッチャー（Noneの場合は.gitignoreを適用しない）

Returns:
    全API情報のリスト

*定義場所: docgen/generators/parsers/base_parser.py:112*

---


## docgen/generators/parsers/generic_parser.py

### GenericParser

**型**: `class`

**シグネチャ**:
```
class GenericParser:
```

**説明**:

汎用コード解析クラス

*定義場所: docgen/generators/parsers/generic_parser.py:16*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, project_root: Path, language: str):
```

**説明**:

初期化

Args:
    project_root: プロジェクトのルートディレクトリ
    language: 言語名（'rust', 'java', 'c', 'cpp', 'go', 'ruby', 'php'など）

*定義場所: docgen/generators/parsers/generic_parser.py:36*

---

### get_supported_extensions

**型**: `method`

**シグネチャ**:
```
def get_supported_extensions(self) -> list[str]:
```

**説明**:

サポートする拡張子を返す
DetectorPatternsから拡張子を取得して一元管理

Returns:
    言語に応じた拡張子のリスト

*定義場所: docgen/generators/parsers/generic_parser.py:170*

---


## docgen/generators/parsers/js_parser.py

### JSParser

**型**: `class`

**シグネチャ**:
```
class JSParser:
```

**説明**:

JavaScript/TypeScriptコード解析クラス

*定義場所: docgen/generators/parsers/js_parser.py:17*

---

### get_supported_extensions

**型**: `method`

**シグネチャ**:
```
def get_supported_extensions(self) -> list[str]:
```

**説明**:

サポートする拡張子を返す

*定義場所: docgen/generators/parsers/js_parser.py:233*

---


## docgen/generators/parsers/parser_patterns.py

### ParserPatterns

**型**: `class`

**シグネチャ**:
```
class ParserPatterns:
```

**説明**:

Common patterns and utilities for code parsing.

*定義場所: docgen/generators/parsers/parser_patterns.py:9*

---

### extract_docstring

**型**: `method`

**シグネチャ**:
```
def extract_docstring(cls, content: str, language: str, start_pos: int) -> str | None:
```

**説明**:

Extract docstring/comment from content starting at a position.

Args:
    content: Source code content
    language: Programming language
    start_pos: Position to start searching from

Returns:
    Extracted docstring or None

*定義場所: docgen/generators/parsers/parser_patterns.py:53*

---

### find_functions_and_classes

**型**: `method`

**シグネチャ**:
```
def find_functions_and_classes(cls, content: str, language: str) -> list[tuple[str, str, int]]:
```

**説明**:

Find all functions and classes in content.

Args:
    content: Source code content
    language: Programming language

Returns:
    List of (name, type, position) tuples

*定義場所: docgen/generators/parsers/parser_patterns.py:74*

---

### create_api_info

**型**: `method`

**シグネチャ**:
```
def create_api_info(cls, name: str, entity_type: str, file_path: Path, project_root: Path, line_number: int | None, signature: str | None, docstring: str | None, language: str | None) -> APIInfo:
```

**説明**:

Create APIInfo object with common fields.

Args:
    name: Function/class name
    entity_type: Type ('function', 'class', etc.)
    file_path: Source file path
    project_root: Project root path
    line_number: Line number (optional)
    signature: Function signature (optional)
    docstring: Documentation string (optional)
    language: Programming language (optional, inferred from file extension if not provided)

Returns:
    APIInfo object

*定義場所: docgen/generators/parsers/parser_patterns.py:98*

---

### clean_docstring

**型**: `method`

**シグネチャ**:
```
def clean_docstring(cls, docstring: str, language: str) -> str:
```

**説明**:

Clean and normalize docstring content.

Args:
    docstring: Raw docstring
    language: Programming language

Returns:
    Cleaned docstring

*定義場所: docgen/generators/parsers/parser_patterns.py:154*

---


## docgen/generators/parsers/python_parser.py

### PythonParser

**型**: `class`

**シグネチャ**:
```
class PythonParser:
```

**説明**:

Pythonコード解析クラス

*定義場所: docgen/generators/parsers/python_parser.py:30*

---

### get_supported_extensions

**型**: `method`

**シグネチャ**:
```
def get_supported_extensions(self) -> list[str]:
```

**説明**:

サポートする拡張子を返す

*定義場所: docgen/generators/parsers/python_parser.py:51*

---

### PythonASTVisitor

**型**: `class`

**シグネチャ**:
```
class PythonASTVisitor:
```

**説明**:

Python AST訪問クラス

*定義場所: docgen/generators/parsers/python_parser.py:58*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, file_path: Path, project_root: Path):
```

*説明なし*

*定義場所: docgen/generators/parsers/python_parser.py:61*

---

### visit_ClassDef

**型**: `method`

**シグネチャ**:
```
def visit_ClassDef(self, node: ast.ClassDef):
```

*説明なし*

*定義場所: docgen/generators/parsers/python_parser.py:67*

---

### visit_FunctionDef

**型**: `method`

**シグネチャ**:
```
def visit_FunctionDef(self, node):
```

*説明なし*

*定義場所: docgen/generators/parsers/python_parser.py:91*

---

### visit_AsyncFunctionDef

**型**: `method`

**シグネチャ**:
```
def visit_AsyncFunctionDef(self, node):
```

*説明なし*

*定義場所: docgen/generators/parsers/python_parser.py:94*

---


## docgen/generators/readme_generator.py

### ReadmeGenerator

**型**: `class`

**シグネチャ**:
```
class ReadmeGenerator:
```

**説明**:

README generation class

*定義場所: docgen/generators/readme_generator.py:17*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, project_root: Path, languages: list[str], config: dict[str, Any], package_managers: dict[str, str] | None):
```

**説明**:

Initialize

Args:
    project_root: Project root directory
    languages: List of detected languages
    config: Configuration dictionary
    package_managers: Dictionary of detected package managers
    **kwargs: Additional arguments passed to BaseGenerator (services, etc.)

*定義場所: docgen/generators/readme_generator.py:20*

---

### readme_path

**型**: `method`

**シグネチャ**:
```
def readme_path(self):
```

*説明なし*

*定義場所: docgen/generators/readme_generator.py:48*

---


## docgen/hooks/config.py

### TaskConfig

**型**: `class`

**シグネチャ**:
```
class TaskConfig:
```

**説明**:

タスク設定

*定義場所: docgen/hooks/config.py:21*

---

### HookConfig

**型**: `class`

**シグネチャ**:
```
class HookConfig:
```

**説明**:

フック設定

*定義場所: docgen/hooks/config.py:32*

---

### ConfigLoader

**型**: `class`

**シグネチャ**:
```
class ConfigLoader:
```

**説明**:

フック設定ローダー

*定義場所: docgen/hooks/config.py:40*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, project_root: str):
```

*説明なし*

*定義場所: docgen/hooks/config.py:43*

---

### load_config

**型**: `method`

**シグネチャ**:
```
def load_config(self) -> dict[str, HookConfig]:
```

**説明**:

設定を読み込む

*定義場所: docgen/hooks/config.py:48*

---


## docgen/hooks/orchestrator.py

### HookOrchestrator

**型**: `class`

**シグネチャ**:
```
class HookOrchestrator:
```

**説明**:

Git hook実行のオーケストレーター

*定義場所: docgen/hooks/orchestrator.py:20*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, hook_name: str, args: list[str] | None):
```

*説明なし*

*定義場所: docgen/hooks/orchestrator.py:23*

---

### register_task

**型**: `method`

**シグネチャ**:
```
def register_task(self, name: str, task_class: type):
```

**説明**:

タスクを登録する

*定義場所: docgen/hooks/orchestrator.py:41*

---

### run_async

**型**: `method`

**シグネチャ**:
```
async def run_async(self) -> int:
```

**説明**:

フックを非同期実行する

*定義場所: docgen/hooks/orchestrator.py:45*

---

### run

**型**: `method`

**シグネチャ**:
```
def run(self) -> int:
```

**説明**:

同期実行ラッパー

*定義場所: docgen/hooks/orchestrator.py:123*

---

### main

**型**: `function`

**シグネチャ**:
```
def main():
```

**説明**:

エントリーポイント

*定義場所: docgen/hooks/orchestrator.py:128*

---


## docgen/language_detector.py

### LanguageDetector

**型**: `class`

**シグネチャ**:
```
class LanguageDetector:
```

**説明**:

言語検出クラス

*定義場所: docgen/language_detector.py:18*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, project_root: Path, config_manager):
```

**説明**:

初期化

Args:
    project_root: プロジェクトルートパス
    config_manager: 設定マネージャー（Noneの場合は新規作成）

*定義場所: docgen/language_detector.py:21*

---

### detect_languages

**型**: `method`

**シグネチャ**:
```
def detect_languages(self, use_parallel: bool) -> list[DetectedLanguage]:
```

**説明**:

プロジェクトの使用言語を自動検出

Args:
    use_parallel: 並列処理を使用するかどうか（デフォルト: True）

Returns:
    検出された言語オブジェクトのリスト

*定義場所: docgen/language_detector.py:74*

---

### get_detected_languages

**型**: `method`

**シグネチャ**:
```
def get_detected_languages(self) -> list[str]:
```

**説明**:

検出された言語名のリストを取得（後方互換性用）

*定義場所: docgen/language_detector.py:214*

---

### get_detected_language_objects

**型**: `method`

**シグネチャ**:
```
def get_detected_language_objects(self) -> list[DetectedLanguage]:
```

**説明**:

検出された言語オブジェクトのリストを取得

*定義場所: docgen/language_detector.py:218*

---

### get_detected_package_managers

**型**: `method`

**シグネチャ**:
```
def get_detected_package_managers(self) -> dict[str, str]:
```

**説明**:

検出されたパッケージマネージャを取得

*定義場所: docgen/language_detector.py:222*

---


## docgen/models/config.py

### GeneralConfig

**型**: `class`

**シグネチャ**:
```
class GeneralConfig:
```

**説明**:

General configuration model.

*定義場所: docgen/models/config.py:11*

---

### MessagesConfig

**型**: `class`

**シグネチャ**:
```
class MessagesConfig:
```

**説明**:

Messages configuration model.

*定義場所: docgen/models/config.py:17*

---

### TechnicalKeywordsConfig

**型**: `class`

**シグネチャ**:
```
class TechnicalKeywordsConfig:
```

**説明**:

Technical keywords configuration model.

*定義場所: docgen/models/config.py:23*

---

### ValidatorConfig

**型**: `class`

**シグネチャ**:
```
class ValidatorConfig:
```

**説明**:

Validator configuration model.

*定義場所: docgen/models/config.py:54*

---

### ImplementationValidationConfig

**型**: `class`

**シグネチャ**:
```
class ImplementationValidationConfig:
```

**説明**:

Implementation validation configuration model.

*定義場所: docgen/models/config.py:60*

---

### ValidationConfig

**型**: `class`

**シグネチャ**:
```
class ValidationConfig:
```

**説明**:

Validation configuration model.

*定義場所: docgen/models/config.py:69*

---

### LanguagesConfig

**型**: `class`

**シグネチャ**:
```
class LanguagesConfig:
```

**説明**:

Languages configuration model.

*定義場所: docgen/models/config.py:82*

---

### OutputConfig

**型**: `class`

**シグネチャ**:
```
class OutputConfig:
```

**説明**:

Output configuration model.

*定義場所: docgen/models/config.py:90*

---

### GenerationConfig

**型**: `class`

**シグネチャ**:
```
class GenerationConfig:
```

**説明**:

Generation configuration model.

*定義場所: docgen/models/config.py:98*

---

### ExcludeConfig

**型**: `class`

**シグネチャ**:
```
class ExcludeConfig:
```

**説明**:

Exclude configuration model.

*定義場所: docgen/models/config.py:107*

---

### CacheConfig

**型**: `class`

**シグネチャ**:
```
class CacheConfig:
```

**説明**:

Cache configuration model.

*定義場所: docgen/models/config.py:115*

---

### BenchmarkConfig

**型**: `class`

**シグネチャ**:
```
class BenchmarkConfig:
```

**説明**:

Benchmark configuration model.

*定義場所: docgen/models/config.py:121*

---

### DebugConfig

**型**: `class`

**シグネチャ**:
```
class DebugConfig:
```

**説明**:

Debug configuration model.

*定義場所: docgen/models/config.py:127*

---

### EmbeddingConfig

**型**: `class`

**シグネチャ**:
```
class EmbeddingConfig:
```

**説明**:

Embedding configuration model.

*定義場所: docgen/models/config.py:133*

---

### IndexConfig

**型**: `class`

**シグネチャ**:
```
class IndexConfig:
```

**説明**:

Index configuration model.

*定義場所: docgen/models/config.py:140*

---

### RetrievalConfig

**型**: `class`

**シグネチャ**:
```
class RetrievalConfig:
```

**説明**:

Retrieval configuration model.

*定義場所: docgen/models/config.py:148*

---

### ChunkingConfig

**型**: `class`

**シグネチャ**:
```
class ChunkingConfig:
```

**説明**:

Chunking configuration model.

*定義場所: docgen/models/config.py:156*

---

### RagExcludeConfig

**型**: `class`

**シグネチャ**:
```
class RagExcludeConfig:
```

*説明なし*

*定義場所: docgen/models/config.py:163*

---

### RagConfig

**型**: `class`

**シグネチャ**:
```
class RagConfig:
```

**説明**:

RAG configuration model.

*定義場所: docgen/models/config.py:175*

---

### ArchitecturePythonConfig

**型**: `class`

**シグネチャ**:
```
class ArchitecturePythonConfig:
```

**説明**:

Python architecture configuration.

*定義場所: docgen/models/config.py:187*

---

### ArchitectureJavascriptConfig

**型**: `class`

**シグネチャ**:
```
class ArchitectureJavascriptConfig:
```

**説明**:

JavaScript architecture configuration.

*定義場所: docgen/models/config.py:194*

---

### ArchitectureConfig

**型**: `class`

**シグネチャ**:
```
class ArchitectureConfig:
```

**説明**:

Architecture diagram generation configuration.

*定義場所: docgen/models/config.py:200*

---

### DocgenConfig

**型**: `class`

**シグネチャ**:
```
class DocgenConfig:
```

**説明**:

Main configuration model for docgen.

*定義場所: docgen/models/config.py:211*

---


## docgen/rag/indexer.py

### VectorIndexer

**型**: `class`

**シグネチャ**:
```
class VectorIndexer:
```

**説明**:

ベクトルインデックス管理クラス

*定義場所: docgen/rag/indexer.py:16*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, index_dir: Path, embedding_dim: int, config: dict[str, Any] | None, logger: Logger | None):
```

**説明**:

初期化

Args:
    index_dir: インデックス保存ディレクトリ
    embedding_dim: 埋め込みベクトルの次元数
    config: RAG設定（config.toml の rag セクション）
    logger: ロガーインスタンス（Noneの場合は新規作成）

*定義場所: docgen/rag/indexer.py:19*

---

### build

**型**: `method`

**シグネチャ**:
```
def build(self, embeddings: np.ndarray, metadata: list[dict[str, Any]]):
```

**説明**:

インデックスを構築

Args:
    embeddings: 埋め込みベクトルの配列（shape: [n_samples, embedding_dim]）
    metadata: 各埋め込みに対応するメタデータのリスト

*定義場所: docgen/rag/indexer.py:50*

---

### save

**型**: `method`

**シグネチャ**:
```
def save(self):
```

**説明**:

インデックスとメタデータを保存

*定義場所: docgen/rag/indexer.py:101*

---

### load

**型**: `method`

**シグネチャ**:
```
def load(self):
```

**説明**:

インデックスとメタデータを読み込み

*定義場所: docgen/rag/indexer.py:130*

---

### search

**型**: `method`

**シグネチャ**:
```
def search(self, query_embedding: np.ndarray, k: int) -> list[tuple[dict[str, Any], float]]:
```

**説明**:

類似ベクトルを検索

Args:
    query_embedding: クエリの埋め込みベクトル
    k: 取得する件数

Returns:
    (メタデータ, スコア) のタプルのリスト

*定義場所: docgen/rag/indexer.py:170*

---

### incremental_update

**型**: `method`

**シグネチャ**:
```
def incremental_update(self, new_embeddings: np.ndarray, new_metadata: list[dict[str, Any]]):
```

**説明**:

インデックスに新しいデータを追加（増分更新）

Args:
    new_embeddings: 新しい埋め込みベクトル
    new_metadata: 新しいメタデータ

*定義場所: docgen/rag/indexer.py:200*

---


## docgen/rag/retriever.py

### DocumentRetriever

**型**: `class`

**シグネチャ**:
```
class DocumentRetriever:
```

**説明**:

ドキュメント検索クラス

*定義場所: docgen/rag/retriever.py:15*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, config: dict[str, Any], project_root: Path | None, logger: Logger | None):
```

**説明**:

初期化

Args:
    config: 設定辞書（config.toml全体）
    project_root: プロジェクトルート（指定しない場合は現在のディレクトリ）
    logger: ロガーインスタンス（Noneの場合は新規作成）

*定義場所: docgen/rag/retriever.py:18*

---

### embedder

**型**: `method`

**シグネチャ**:
```
def embedder(self) -> Embedder:
```

**説明**:

Embedderインスタンスを取得（Lazy loading）

*定義場所: docgen/rag/retriever.py:51*

---

### indexer

**型**: `method`

**シグネチャ**:
```
def indexer(self) -> VectorIndexer:
```

**説明**:

VectorIndexerインスタンスを取得（Lazy loading）

*定義場所: docgen/rag/retriever.py:58*

---

### retrieve

**型**: `method`

**シグネチャ**:
```
def retrieve(self, query: str, top_k: int | None) -> list[dict[str, Any]]:
```

**説明**:

クエリに類似するチャンクを検索

Args:
    query: 検索クエリ
    top_k: 取得する件数（Noneの場合はデフォルト値）

Returns:
    チャンクのリスト（スコア付き）

*定義場所: docgen/rag/retriever.py:84*

---

### format_context

**型**: `method`

**シグネチャ**:
```
def format_context(self, chunks: list[dict[str, Any]]) -> str:
```

**説明**:

チャンクをコンテキスト文字列にフォーマット

Args:
    chunks: チャンクのリスト

Returns:
    フォーマット済みのコンテキスト文字列

*定義場所: docgen/rag/retriever.py:184*

---

### retrieve_with_rerank

**型**: `method`

**シグネチャ**:
```
def retrieve_with_rerank(self, query: str, top_k: int, rerank_k: int) -> list[dict[str, Any]]:
```

**説明**:

再ランキング付き検索（将来の拡張用）

Args:
    query: 検索クエリ
    top_k: 最終的に取得する件数
    rerank_k: 初期検索で取得する件数（再ランク対象）

Returns:
    再ランク済みのチャンクのリスト

*定義場所: docgen/rag/retriever.py:216*

---


## docgen/rag/strategies/code_strategy.py

### CodeChunkStrategy

**型**: `class`

**シグネチャ**:
```
class CodeChunkStrategy:
```

**説明**:

Strategy for chunking code files (Python, JavaScript/TypeScript, YAML, TOML).

*定義場所: docgen/rag/strategies/code_strategy.py:16*

---

### chunk

**型**: `method`

**シグネチャ**:
```
def chunk(self, content: str, file_path: Path) -> list[dict[str, Any]]:
```

**説明**:

Chunk code content based on file extension.

*定義場所: docgen/rag/strategies/code_strategy.py:19*

---


## docgen/rag/strategies/markdown_strategy.py

### MarkdownChunkStrategy

**型**: `class`

**シグネチャ**:
```
class MarkdownChunkStrategy:
```

**説明**:

Strategy for chunking Markdown files.

*定義場所: docgen/rag/strategies/markdown_strategy.py:11*

---

### chunk

**型**: `method`

**シグネチャ**:
```
def chunk(self, content: str, file_path: Path) -> list[dict[str, Any]]:
```

**説明**:

Chunk Markdown files by headers.

*定義場所: docgen/rag/strategies/markdown_strategy.py:14*

---


## docgen/rag/validator.py

### DocumentValidator

**型**: `class`

**シグネチャ**:
```
class DocumentValidator:
```

**説明**:

ドキュメント検証クラス

*定義場所: docgen/rag/validator.py:15*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, project_root: Path | None, config: dict[str, Any] | None):
```

**説明**:

初期化

Args:
    project_root: プロジェクトルート
    config: 設定辞書（技術キーワードの設定を含む）

*定義場所: docgen/rag/validator.py:54*

---

### validate_citations

**型**: `method`

**シグネチャ**:
```
def validate_citations(self, document: str, strict: bool) -> list[str]:
```

**説明**:

ドキュメント内の出典を検証

Args:
    document: 検証対象のドキュメント
    strict: 厳格モード（技術的主張に出典がない場合もエラー）

Returns:
    エラーメッセージのリスト

*定義場所: docgen/rag/validator.py:99*

---

### detect_secrets

**型**: `method`

**シグネチャ**:
```
def detect_secrets(self, document: str) -> list[str]:
```

**説明**:

ドキュメント内の機密情報を検出

Args:
    document: 検証対象のドキュメント

Returns:
    警告メッセージのリスト

*定義場所: docgen/rag/validator.py:179*

---

### validate

**型**: `method`

**シグネチャ**:
```
def validate(self, document: str, check_citations: bool, check_secrets: bool, strict: bool) -> dict[str, Any]:
```

**説明**:

ドキュメントの総合検証

Args:
    document: 検証対象のドキュメント
    check_citations: 出典チェックを行うか
    check_secrets: 機密情報チェックを行うか
    strict: 厳格モード

Returns:
    検証結果の辞書

*定義場所: docgen/rag/validator.py:214*

---

### print_report

**型**: `method`

**シグネチャ**:
```
def print_report(self, validation_result: dict[str, Any]):
```

**説明**:

検証結果をコンソールに出力

*定義場所: docgen/rag/validator.py:260*

---


## docgen/utils/cache.py

### CacheManager

**型**: `class`

**シグネチャ**:
```
class CacheManager:
```

**説明**:

キャッシュ管理クラス

*定義場所: docgen/utils/cache.py:20*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, project_root: Path, cache_dir: Path | None, enabled: bool):
```

**説明**:

初期化

Args:
    project_root: プロジェクトのルートディレクトリ
    cache_dir: キャッシュディレクトリ（Noneの場合は`docgen/.cache/`）
    enabled: キャッシュを有効にするかどうか

*定義場所: docgen/utils/cache.py:23*

---

### get_file_hash

**型**: `method`

**シグネチャ**:
```
def get_file_hash(self, file_path: Path) -> str:
```

**説明**:

ファイルのハッシュを計算

Args:
    file_path: ファイルパス

Returns:
    ファイルのSHA256ハッシュ（16進数文字列）

*定義場所: docgen/utils/cache.py:78*

---

### get_cache_key

**型**: `method`

**シグネチャ**:
```
def get_cache_key(self, file_path: Path, parser_type: str) -> str:
```

**説明**:

キャッシュキーを生成

Args:
    file_path: ファイルパス（相対パスまたは絶対パス）
    parser_type: パーサーの種類（例: 'python', 'javascript'）

Returns:
    キャッシュキー

*定義場所: docgen/utils/cache.py:99*

---

### get_cached_result

**型**: `method`

**シグネチャ**:
```
def get_cached_result(self, file_path: Path, parser_type: str) -> list[APIInfo] | None:
```

**説明**:

キャッシュから結果を取得

Args:
    file_path: ファイルパス
    parser_type: パーサーの種類

Returns:
    キャッシュされた結果（存在する場合）、またはNone

*定義場所: docgen/utils/cache.py:124*

---

### set_cached_result

**型**: `method`

**シグネチャ**:
```
def set_cached_result(self, file_path: Path, parser_type: str, result: list[APIInfo]) -> None:
```

**説明**:

結果をキャッシュに保存

Args:
    file_path: ファイルパス
    parser_type: パーサーの種類
    result: 解析結果

*定義場所: docgen/utils/cache.py:183*

---

### clear_cache

**型**: `method`

**シグネチャ**:
```
def clear_cache(self) -> None:
```

**説明**:

キャッシュをクリア

*定義場所: docgen/utils/cache.py:215*

---

### invalidate_file

**型**: `method`

**シグネチャ**:
```
def invalidate_file(self, file_path: Path, parser_type: str | None) -> None:
```

**説明**:

特定のファイルのキャッシュを無効化

Args:
    file_path: ファイルパス
    parser_type: パーサーの種類（Noneの場合はすべてのパーサータイプ）

*定義場所: docgen/utils/cache.py:222*

---

### save

**型**: `method`

**シグネチャ**:
```
def save(self) -> None:
```

**説明**:

キャッシュを保存（明示的に保存する場合）

*定義場所: docgen/utils/cache.py:258*

---

### get_cache_stats

**型**: `method`

**シグネチャ**:
```
def get_cache_stats(self) -> dict[str, Any]:
```

**説明**:

キャッシュの統計情報を取得

Returns:
    統計情報の辞書

*定義場所: docgen/utils/cache.py:262*

---


## docgen/utils/file_utils.py

### safe_read_file

**型**: `function`

**シグネチャ**:
```
def safe_read_file(file_path: Path, encoding: str) -> str | None:
```

**説明**:

ファイルを安全に読み込む

Args:
    file_path: 読み込むファイルのパス
    encoding: 文字エンコーディング

Returns:
    ファイルの内容。読み込み失敗時はNone

*定義場所: docgen/utils/file_utils.py:20*

---

### save_yaml_file

**型**: `function`

**シグネチャ**:
```
def save_yaml_file(file_path: Path, data: dict[str, Any]) -> bool:
```

**説明**:

YAMLファイルを保存

Args:
    file_path: 保存先ファイルパス
    data: 保存するデータ

Returns:
    成功した場合はTrue

*定義場所: docgen/utils/file_utils.py:39*

---

### save_toml_file

**型**: `function`

**シグネチャ**:
```
def save_toml_file(file_path: Path, content: str) -> bool:
```

**説明**:

TOMLファイルを保存

Args:
    file_path: 保存先ファイルパス
    content: TOML形式の文字列

Returns:
    成功した場合はTrue

*定義場所: docgen/utils/file_utils.py:61*

---

### safe_write_file

**型**: `function`

**シグネチャ**:
```
def safe_write_file(file_path: Path, content: str, encoding: str) -> bool:
```

**説明**:

ファイルを安全に書き込む

Args:
    file_path: 書き込むファイルのパス
    content: 書き込む内容
    encoding: 文字エンコーディング

Returns:
    成功した場合はTrue

*定義場所: docgen/utils/file_utils.py:80*

---

### safe_read_json

**型**: `function`

**シグネチャ**:
```
def safe_read_json(file_path: Path) -> Any | None:
```

**説明**:

JSONファイルを安全に読み込む

Args:
    file_path: JSONファイルのパス

Returns:
    パースされたJSONデータ。失敗時はNone

*定義場所: docgen/utils/file_utils.py:100*

---

### find_files_with_extensions

**型**: `function`

**シグネチャ**:
```
def find_files_with_extensions(root_dir: Path, extensions: list[str]) -> list[Path]:
```

**説明**:

指定された拡張子のファイルを検索

Args:
    root_dir: 検索するルートディレクトリ
    extensions: 拡張子のリスト（例: ['.py', '.js']）

Returns:
    見つかったファイルのリスト

*定義場所: docgen/utils/file_utils.py:119*

---

### safe_read_yaml

**型**: `function`

**シグネチャ**:
```
def safe_read_yaml(file_path: Path) -> Any | None:
```

**説明**:

YAMLファイルを安全に読み込む

Args:
    file_path: YAMLファイルのパス

Returns:
    パースされたYAMLデータ。失敗時はNone

*定義場所: docgen/utils/file_utils.py:136*

---

### safe_read_toml

**型**: `function`

**シグネチャ**:
```
def safe_read_toml(file_path: Path) -> Any | None:
```

**説明**:

TOMLファイルを安全に読み込む

Args:
    file_path: TOMLファイルのパス

Returns:
    パースされたTOMLデータ。失敗時はNone

Raises:
    tomllib.TOMLDecodeError: TOMLパースエラーが発生した場合（詳細なエラー情報を含む）

*定義場所: docgen/utils/file_utils.py:157*

---


## docgen/utils/llm/anthropic_client.py

### AnthropicClient

**型**: `class`

**シグネチャ**:
```
class AnthropicClient:
```

**説明**:

Anthropic APIクライアント

*定義場所: docgen/utils/llm/anthropic_client.py:14*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, config: dict[str, Any]):
```

*説明なし*

*定義場所: docgen/utils/llm/anthropic_client.py:17*

---

### generate

**型**: `method`

**シグネチャ**:
```
def generate(self, prompt: str, system_prompt: str | None) -> str | None:
```

**説明**:

Anthropic APIを使用してテキストを生成

*定義場所: docgen/utils/llm/anthropic_client.py:39*

---


## docgen/utils/llm/base.py

### LLMClientInitializer

**型**: `class`

**シグネチャ**:
```
class LLMClientInitializer:
```

**説明**:

Common initialization patterns for LLM clients.

*定義場所: docgen/utils/llm/base.py:25*

---

### setup_provider_config

**型**: `method`

**シグネチャ**:
```
def setup_provider_config(config: dict[str, Any], provider: str) -> dict[str, Any]:
```

**説明**:

Set up provider-specific configuration.

Args:
    config: Configuration dictionary
    provider: Provider name ('openai', 'anthropic', etc.)

Returns:
    Updated configuration dictionary

*定義場所: docgen/utils/llm/base.py:29*

---

### get_api_key

**型**: `method`

**シグネチャ**:
```
def get_api_key(config, env_var: str, default_env: str) -> str:
```

**説明**:

Get API key from config or environment.

Args:
    config: LLMConfig object
    env_var: Environment variable name from config
    default_env: Default environment variable name

Returns:
    API key string

*定義場所: docgen/utils/llm/base.py:46*

---

### initialize_client_with_fallback

**型**: `method`

**シグネチャ**:
```
def initialize_client_with_fallback(client_class, config: dict[str, Any], import_name: str, package_name: str, error_prefix: str):
```

**説明**:

Initialize LLM client with common error handling.

Args:
    client_class: Client class to instantiate
    config: Configuration dictionary
    import_name: Module name to import
    package_name: Package name for error messages
    error_prefix: Prefix for error messages

Returns:
    Initialized client instance

Raises:
    ImportError: If required package is not installed
    ConfigError: If initialization fails

*定義場所: docgen/utils/llm/base.py:63*

---

### BaseLLMClient

**型**: `class`

**シグネチャ**:
```
class BaseLLMClient:
```

**説明**:

LLMクライアントの抽象基底クラス

*定義場所: docgen/utils/llm/base.py:100*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, config: dict[str, Any] | LLMConfig):
```

**説明**:

初期化

Args:
    config: LLM設定辞書またはLLMConfigオブジェクト

*定義場所: docgen/utils/llm/base.py:103*

---

### generate

**型**: `method`

**シグネチャ**:
```
def generate(self, prompt: str, system_prompt: str | None) -> str | None:
```

**説明**:

テキストを生成

Args:
    prompt: プロンプト
    system_prompt: システムプロンプト（オプション）
    **kwargs: その他のパラメータ

Returns:
    生成されたテキスト（エラー時はNone）

*定義場所: docgen/utils/llm/base.py:120*

---

### create_outlines_model

**型**: `method`

**シグネチャ**:
```
def create_outlines_model(self):
```

**説明**:

Outlinesモデルを作成

Returns:
    Outlinesモデルインスタンス（Outlinesが利用できない場合はNone）

*定義場所: docgen/utils/llm/base.py:134*

---


## docgen/utils/llm/factory.py

### LLMClientFactory

**型**: `class`

**シグネチャ**:
```
class LLMClientFactory:
```

**説明**:

LLMクライアントのファクトリークラス

*定義場所: docgen/utils/llm/factory.py:18*

---

### create_client

**型**: `method`

**シグネチャ**:
```
def create_client(config: dict[str, Any] | LLMClientConfig, mode: str) -> BaseLLMClient | None:
```

**説明**:

LLMクライアントを作成

Args:
    config: LLM設定辞書またはLLMClientConfigオブジェクト
    mode: 'api' または 'local'

Returns:
    LLMクライアントインスタンス（エラー時はNone）

*定義場所: docgen/utils/llm/factory.py:22*

---

### create_client_with_fallback

**型**: `method`

**シグネチャ**:
```
def create_client_with_fallback(config: dict[str, Any], preferred_mode: str) -> BaseLLMClient | None:
```

**説明**:

LLMクライアントを作成（フォールバック付き）

Args:
    config: LLM設定辞書
    preferred_mode: 優先するモード（'api' または 'local'）

Returns:
    LLMクライアントインスタンス（エラー時はNone）

*定義場所: docgen/utils/llm/factory.py:86*

---


## docgen/utils/llm/local_client.py

### LocalLLMClient

**型**: `class`

**シグネチャ**:
```
class LocalLLMClient:
```

**説明**:

ローカルLLMクライアント（Ollama、LM Studio対応）

*定義場所: docgen/utils/llm/local_client.py:14*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, config: dict[str, Any]):
```

*説明なし*

*定義場所: docgen/utils/llm/local_client.py:17*

---

### generate

**型**: `method`

**シグネチャ**:
```
def generate(self, prompt: str, system_prompt: str | None) -> str | None:
```

**説明**:

ローカルLLMを使用してテキストを生成

*定義場所: docgen/utils/llm/local_client.py:43*

---


## docgen/utils/llm/openai_client.py

### OpenAIClient

**型**: `class`

**シグネチャ**:
```
class OpenAIClient:
```

**説明**:

OpenAI APIクライアント

*定義場所: docgen/utils/llm/openai_client.py:14*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, config: dict[str, Any]):
```

*説明なし*

*定義場所: docgen/utils/llm/openai_client.py:17*

---

### generate

**型**: `method`

**シグネチャ**:
```
def generate(self, prompt: str, system_prompt: str | None) -> str | None:
```

**説明**:

OpenAI APIを使用してテキストを生成

*定義場所: docgen/utils/llm/openai_client.py:41*

---


## docgen/utils/markdown_utils.py

### get_current_timestamp

**型**: `function`

**シグネチャ**:
```
def get_current_timestamp() -> str:
```

**説明**:

Get current timestamp in standard format.

*定義場所: docgen/utils/markdown_utils.py:32*

---

### extract_project_description

**型**: `function`

**シグネチャ**:
```
def extract_project_description(project_root: Path, project_info_description: str | None, exclude_readme_path: Path | None, config: dict[str, Any] | None) -> str:
```

**説明**:

Extract project description from package manager files or README.md.

Priority order:
1. package.json (if exists)
2. pyproject.toml (if exists)
3. setup.py (if exists)
4. project_info_description (from LanguageInfoCollector)
5. README.md (if not excluded)
6. Default message

Args:
    project_root: Project root directory
    project_info_description: Description from project info (already prioritized by package manager)
    exclude_readme_path: README path to exclude (to prevent circular reference)
    config: Configuration dictionary (for multilingual messages)

Returns:
    Project description text

*定義場所: docgen/utils/markdown_utils.py:141*

---

### clean_llm_output_advanced

**型**: `function`

**シグネチャ**:
```
def clean_llm_output_advanced(text: str) -> str:
```

**説明**:

Advanced LLM output cleaning with thinking process removal and code block handling.

Args:
    text: LLM generated text to clean

Returns:
    Cleaned text with thinking processes removed

*定義場所: docgen/utils/markdown_utils.py:202*

---


## docgen/utils/outlines_utils.py

### should_use_outlines

**型**: `function`

**シグネチャ**:
```
def should_use_outlines(config: dict[str, Any]) -> bool:
```

**説明**:

Outlinesを使用するかどうかを判定

Args:
    config: 設定辞書

Returns:
    Outlinesを使用するかどうか

*定義場所: docgen/utils/outlines_utils.py:20*

---

### create_outlines_model

**型**: `function`

**シグネチャ**:
```
def create_outlines_model(client, provider: str):
```

**説明**:

Outlinesモデルを作成

Args:
    client: LLMクライアント
    provider: プロバイダー名 ('openai', 'anthropic', 'local')

Returns:
    Outlinesモデルインスタンス（作成できない場合はNone）

*定義場所: docgen/utils/outlines_utils.py:38*

---


## docgen/utils/prompt_loader.py

### PromptLoader

**型**: `class`

**シグネチャ**:
```
class PromptLoader:
```

**説明**:

プロンプトをTOMLファイルから読み込むクラス

*定義場所: docgen/utils/prompt_loader.py:29*

---

### load_prompt

**型**: `method`

**シグネチャ**:
```
def load_prompt(cls, file_name: str, key: str, language: str | None, config: dict[str, Any] | None) -> str:
```

**説明**:

プロンプトを読み込む（多言語対応）

Args:
    file_name: TOMLファイル名（例: 'agents_prompts.toml'）
    key: プロンプトのキー（例: 'overview', 'full'）
    language: 言語コード（Noneの場合は設定から取得）
    config: 設定辞書
    **kwargs: テンプレート変数の置換用パラメータ

Returns:
    読み込んだプロンプト文字列（テンプレート変数が置換済み）

Raises:
    FileNotFoundError: ファイルが見つからない場合
    KeyError: 指定されたキーが見つからない場合

*定義場所: docgen/utils/prompt_loader.py:157*

---

### load_system_prompt

**型**: `method`

**シグネチャ**:
```
def load_system_prompt(cls, file_name: str, key: str, language: str | None, config: dict[str, Any] | None) -> str:
```

**説明**:

システムプロンプトを読み込む（多言語対応）

Args:
    file_name: TOMLファイル名（例: 'agents_prompts.toml'）
    key: システムプロンプトのキー（例: 'overview', 'generate'）
    language: 言語コード（Noneの場合は設定から取得）
    config: 設定辞書
    **kwargs: テンプレート変数の置換用パラメータ

Returns:
    読み込んだシステムプロンプト文字列（テンプレート変数が置換済み）

Raises:
    FileNotFoundError: ファイルが見つからない場合
    KeyError: 指定されたキーが見つからない場合

*定義場所: docgen/utils/prompt_loader.py:201*

---

### clear_cache

**型**: `method`

**シグネチャ**:
```
def clear_cache(cls):
```

**説明**:

キャッシュをクリア（主にテスト用）

*定義場所: docgen/utils/prompt_loader.py:245*

---


## docgen/validators/implementation_validator.py

### EntityReference

**型**: `class`

**シグネチャ**:
```
class EntityReference:
```

**説明**:

ドキュメント内で参照されているエンティティ

*定義場所: docgen/validators/implementation_validator.py:24*

---

### ValidationResult

**型**: `class`

**シグネチャ**:
```
class ValidationResult:
```

**説明**:

検証結果

*定義場所: docgen/validators/implementation_validator.py:35*

---

### ImplementationValidator

**型**: `class`

**シグネチャ**:
```
class ImplementationValidator:
```

**説明**:

実装検証クラス

ドキュメント内で言及されている関数、クラス、メソッドが
実際のコードベースに存在するかを検証します。

*定義場所: docgen/validators/implementation_validator.py:45*

---

### __init__

**型**: `method`

**シグネチャ**:
```
def __init__(self, project_root: Path, languages: list[str] | None, parsers: list[BaseParser] | None, config: dict[str, Any] | None):
```

**説明**:

初期化

Args:
    project_root: プロジェクトのルートディレクトリ
    languages: 検出された言語のリスト（Noneの場合は自動検出）
    parsers: パーサーのリスト（Noneの場合は自動生成）
    config: 設定辞書

*定義場所: docgen/validators/implementation_validator.py:84*

---

### build_api_index

**型**: `method`

**シグネチャ**:
```
def build_api_index(self) -> dict[str, set[str]]:
```

**説明**:

実装済みAPIのインデックスを構築

Returns:
    {entity_type: {name1, name2, ...}} の形式の辞書

*定義場所: docgen/validators/implementation_validator.py:130*

---

### extract_referenced_entities

**型**: `method`

**シグネチャ**:
```
def extract_referenced_entities(self, document: str) -> list[EntityReference]:
```

**説明**:

ドキュメントから参照されているエンティティを抽出

Args:
    document: 検証対象のドキュメント（Markdown形式）

Returns:
    参照されているエンティティのリスト

*定義場所: docgen/validators/implementation_validator.py:294*

---

### validate_implementation

**型**: `method`

**シグネチャ**:
```
def validate_implementation(self, document: str) -> ValidationResult:
```

**説明**:

実装の存在を検証

Args:
    document: 検証対象のドキュメント

Returns:
    検証結果

*定義場所: docgen/validators/implementation_validator.py:377*

---

### get_implemented_api_summary

**型**: `method`

**シグネチャ**:
```
def get_implemented_api_summary(self) -> str:
```

**説明**:

実装済みAPIのサマリーを取得（LLMプロンプト用）

Returns:
    実装済みAPIのサマリーテキスト

*定義場所: docgen/validators/implementation_validator.py:453*

---

### print_report

**型**: `method`

**シグネチャ**:
```
def print_report(self, validation_result: ValidationResult):
```

**説明**:

検証結果をコンソールに出力

*定義場所: docgen/validators/implementation_validator.py:494*

---


## scripts/verify_language_detector.py

### main

**型**: `function`

**シグネチャ**:
```
def main():
```

*説明なし*

*定義場所: scripts/verify_language_detector.py:12*

---
