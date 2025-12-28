# 開発者向けガイド

このドキュメントは、`agents-docs-sync`プロジェクトに貢献する開発者向けのガイドです。

## 目次

1. [プロジェクトの構造](#プロジェクトの構造)
2. [開発環境のセットアップ](#開発環境のセットアップ)
3. [アーキテクチャ](#アーキテクチャ)
4. [コードの追加方法](#コードの追加方法)
5. [テストの実行](#テストの実行)
6. [コントリビューションガイドライン](#コントリビューションガイドライン)

---

## プロジェクトの構造

```
agents-docs-sync/
├── docgen/                    # メインのドキュメント生成システム
│   ├── detectors/              # 言語検出モジュール
│   │   ├── base_detector.py   # 基底クラス
│   │   ├── python_detector.py
│   │   ├── javascript_detector.py
│   │   ├── go_detector.py
│   │   └── generic_detector.py
│   ├── generators/             # ドキュメント生成モジュール
│   │   ├── api_generator.py   # APIドキュメント生成
│   │   ├── readme_generator.py # README生成
│   │   ├── agents_generator.py # AGENTS.md生成
│   │   └── parsers/            # コードパーサー
│   │       ├── base_parser.py
│   │       ├── python_parser.py
│   │       ├── js_parser.py
│   │       └── generic_parser.py
│   ├── collectors/             # プロジェクト情報収集モジュール
│   │   └── project_info_collector.py
│   ├── utils/                  # ユーティリティ
│   │   └── logger.py           # ロギングモジュール
│   ├── hooks/                  # Git hooks
│   │   ├── pre-commit
│   │   └── post-commit
│   ├── templates/              # Jinja2テンプレート（AGENTS.md, README.md生成用）
│   ├── config.toml.sample      # 設定ファイルのサンプル
│   └── docgen.py               # メインエントリーポイント
├── tests/                      # テストファイル
│   ├── conftest.py             # pytest設定
│   ├── test_docgen.py
│   └── ...
├── scripts/                    # スクリプト
│   ├── generate_requirements.py
│   ├── run_tests.sh
│   └── run_pipeline.sh
├── docs/                       # ドキュメント
│   ├── api.md                  # 自動生成されるAPIドキュメント
│   ├── implementation/         # 実装ドキュメント
│   └── review/                 # レビュードキュメント
├── .github/
│   └── workflows/              # GitHub Actionsワークフロー
│       ├── ci-cd-pipeline.yml
│       └── release.yml
├── pyproject.toml              # プロジェクト設定
├── pytest.ini                   # pytest設定
└── requirements-*.txt          # 依存関係（自動生成）
```

---

## 開発環境のセットアップ

### 前提条件

- Python 3.12以上
- Git
- Bash（スクリプト実行用）

### セットアップ手順

1. **リポジトリのクローン**

```bash
git clone https://github.com/your-username/agents-docs-sync.git
cd agents-docs-sync
```

2. **仮想環境の作成と有効化**

```bash
# uvを使用する場合（推奨）
uv venv
source .venv/bin/activate  # Linux/macOS
# または
.venv\Scripts\activate  # Windows

# または標準のvenvを使用
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
```

3. **依存関係のインストール**

```bash
# requirementsファイルを生成（初回のみ）
python3 scripts/generate_requirements.py

# 依存関係をインストール
pip install -r requirements-docgen.txt
pip install -r requirements-test.txt
```

4. **設定ファイルの作成**

```bash
cp docgen/config.toml.sample docgen/config.toml
# 必要に応じて設定を編集
```

5. **開発用のインストール（オプション）**

```bash
# 開発モードでインストール（コード変更が即座に反映される）
pip install -e .
```

---

## アーキテクチャ

### 主要コンポーネント

#### 1. 言語検出システム（Detectors）

- **目的**: プロジェクトで使用されている言語を自動検出
- **実装**: `BaseDetector`を継承した各言語用の検出器
- **並列処理**: `ThreadPoolExecutor`を使用して並列実行

#### 2. コードパーサー（Parsers）

- **目的**: ソースコードからAPI情報（関数、クラス、シグネチャ、docstring）を抽出
- **実装**: `BaseParser`を継承した各言語用のパーサー
- **並列処理**: ファイル数が10を超える場合、`ThreadPoolExecutor`を使用

#### 3. ドキュメント生成器（Generators）

- **APIGenerator**: `docs/api.md`を生成
- **ReadmeGenerator**: `README.md`を更新（手動セクションを保持、Jinja2テンプレート使用）
- **AgentsGenerator**: `AGENTS.md`を生成（OpenAI仕様準拠、Jinja2テンプレート使用）
- **BaseGenerator**: 共通のテンプレートレンダリング機能を提供

#### 4. サービス層（Services）- DI対応

ジェネレーターは以下のサービスをDIで受け取ります：

| サービス               | 役割                                      |
| ---------------------- | ----------------------------------------- |
| `LLMService`           | LLM連携（プロンプト送信、レスポンス処理） |
| `TemplateService`      | Jinja2テンプレートのレンダリング          |
| `FormattingService`    | テキスト整形、バリデーション              |
| `ManualSectionService` | 手動セクションの抽出・マージ              |
| `RAGService`           | RAGコンテキストの取得                     |

サービスは`GeneratorServiceFactory`で生成され、テスト時にはモックを注入可能です。

#### 5. フックシステム（Hooks）

- **HookOrchestrator**: フック実行のオーケストレーション（非同期対応）
- **TaskRegistry**: デコレータベースのタスク登録
- **HookTask**: 各フックタスクの基底クラス（`run_async`対応）

#### 6. プロジェクト情報収集器（Collectors）

- **目的**: プロジェクトのメタデータ（依存関係、ビルドコマンド、テストコマンドなど）を収集
- **実装**: `ProjectInfoCollector`

### データフロー

```
1. DocGen.detect_languages()
   └─> 各Detectorが並列実行
   └─> 検出された言語のリストを返す

2. DocGen.generate_documents()
   ├─> APIGenerator.generate()
   │   └─> 各Parserがプロジェクトを解析
   │   └─> API情報を収集
   │   └─> Markdownを生成
    ├─> ReadmeGenerator.generate()
    │   └─> 既存READMEから手動セクションを抽出（ManualSectionService）
    │   └─> Jinja2テンプレートで新しいREADMEを生成（TemplateService）
    └─> AgentsGenerator.generate()
        └─> ProjectInfoCollectorで情報収集
        └─> Jinja2テンプレートでMarkdownを生成（TemplateService）
```

---

## コードの追加方法

### 新しい言語のサポートを追加

1. **Detectorの実装**

`docgen/detectors/`に新しい検出器を作成：

```python
from .base_detector import BaseDetector
from pathlib import Path

class NewLanguageDetector(BaseDetector):
    def get_language(self) -> str:
        return "new_language"

    def detect(self) -> bool:
        # 検出ロジックを実装
        # 例: 特定のファイル拡張子や設定ファイルの存在を確認
        return (self.project_root / "new_language.config").exists()
```

2. **Parserの実装**

`docgen/generators/parsers/`に新しいパーサーを作成：

```python
from .base_parser import BaseParser
from pathlib import Path
from typing import List, Dict, Any

class NewLanguageParser(BaseParser):
    def get_supported_extensions(self) -> List[str]:
        return ['.newlang']

    def parse_file(self, file_path: Path) -> List[Dict[str, Any]]:
        # パースロジックを実装
        # API情報を抽出して返す
        apis = []
        # ...
        return apis
```

3. **DocGenクラスに登録**

`docgen/docgen.py`の`detect_languages()`メソッドに検出器を追加：

```python
from .detectors.new_language_detector import NewLanguageDetector

# detect_languages()メソッド内
detectors = [
    # ...
    NewLanguageDetector(self.project_root),
]
```

`api_generator.py`の`_get_parsers()`メソッドにパーサーを追加：

```python
from .parsers.new_language_parser import NewLanguageParser

# _get_parsers()メソッド内
if lang == 'new_language':
    parsers.append(NewLanguageParser(self.project_root))
```

### 新しい機能の追加

1. **機能の設計**
   - 単一責任の原則に従う
   - 既存の抽象基底クラスを活用
   - 型ヒントを適切に使用

2. **テストの作成**
   - `tests/`ディレクトリにテストファイルを作成
   - `@pytest.mark.unit`または`@pytest.mark.integration`マーカーを使用

3. **ドキュメントの更新**
   - コードにdocstringを追加
   - 必要に応じて`docs/`のドキュメントを更新

---

## テストの実行

### すべてのテストを実行

```bash
pytest
# または
python3 -m pytest
```

### 特定のテストを実行

```bash
# ユニットテストのみ
pytest -m unit

# 統合テストのみ
pytest -m integration

# 特定のファイル
pytest tests/test_docgen.py

# 特定のテスト関数
pytest tests/test_docgen.py::test_detect_languages
```

### カバレッジ付きで実行

```bash
pytest --cov=docgen --cov-report=html --cov-report=term-missing
```

カバレッジレポートは`htmlcov/index.html`で確認できます。

### カバレッジ閾値の確認

```bash
pytest --cov=docgen --cov-fail-under=80
```

---

## コントリビューションガイドライン

### コードスタイル

- **PEP 8**に準拠
- 型ヒントを使用（Python 3.12+の機能を活用）
- docstringはGoogle形式を使用

### コミットメッセージ

以下の形式に従ってください：

```
[種類] 簡潔な説明

詳細な説明（必要に応じて）
```

種類の例：
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメントの変更
- `refactor`: リファクタリング
- `test`: テストの追加・変更
- `chore`: ビルドプロセスやツールの変更

### プルリクエストの作成

1. **ブランチの作成**

```bash
git checkout -b feature/your-feature-name
```

2. **変更のコミット**

```bash
git add .
git commit -m "[feat] 新機能の説明"
```

3. **テストの実行**

```bash
pytest
```

4. **プッシュとPR作成**

```bash
git push origin feature/your-feature-name
```

GitHubでプルリクエストを作成し、以下を含めてください：
- 変更内容の説明
- テスト結果
- 関連するIssue番号（あれば）

### レビュープロセス

- すべてのPRはレビューが必要です
- CI/CDパイプラインが成功する必要があります
- テストカバレッジが80%以上を維持する必要があります

---

## トラブルシューティング

### よくある問題

#### 1. インポートエラー

**問題**: `ModuleNotFoundError`が発生する

**解決策**:
- 仮想環境が有効になっているか確認
- `pip install -r requirements-docgen.txt`を実行
- 開発モードでインストール: `pip install -e .`

#### 2. テストが失敗する

**問題**: テストが予期せず失敗する

**解決策**:
- テスト環境が正しくセットアップされているか確認
- `pytest -v`で詳細な出力を確認
- カバレッジレポートを確認して、テストされていないコードがないか確認

#### 3. ドキュメントが生成されない

**問題**: `docs/api.md`や`README.md`が更新されない

**解決策**:
- `docgen/config.toml`が存在し、正しく設定されているか確認
- ログを確認: `python3 docgen/docgen.py --verbose`
- プロジェクトの言語が正しく検出されているか確認: `python3 docgen/docgen.py --detect-only`

---

## 参考資料

- [APIドキュメント](api.md)
- [実装ドキュメント](implementation/)
- [レビューレポート](../REVIEW_REPORT.md)
- [プロジェクトのREADME](../README.md)

---

*最終更新: 2025-01-27*

