# agents-docs-sync プロジェクト管理手順書

## 概要

agents-docs-syncは、Pythonベースのドキュメント自動生成ツールです。プロジェクトのコードを分析し、APIドキュメント、README、AGENTS.mdを自動生成します。

**主要機能:**
- 多言語対応（Python, JavaScript, Go）
- APIドキュメント自動生成
- README自動更新
- AGENTS.md生成（AIコーディングエージェント用）
- GitHub Actions連携

## 開発環境のセットアップ

### 前提条件

- **Python 3.12以上**（必須）
- **uv**（パッケージ管理ツール）

### 環境構築手順

#### 1. リポジトリのクローン
```bash
git clone https://github.com/your-org/agents-docs-sync.git
cd agents-docs-sync
```

#### 2. 依存関係のインストール
```bash
# uvを使用した依存関係インストール
uv sync

# またはpipを使用する場合
pip install -r requirements-docgen.txt
pip install -r requirements-test.txt
```

#### 3. 開発ツールのインストール
```bash
# ruff（リンター/フォーマッター）のインストール確認
uv run ruff --version

# 必要に応じて追加インストール
uv add --dev ruff
```

#### 4. 設定ファイルの準備
```bash
# 設定ファイルのコピー
cp docgen/config.toml.sample docgen/config.toml

# 必要に応じて設定を編集
vim docgen/config.toml
```

#### 5. LLM環境のセットアップ（オプション）
```bash
# OpenAI APIを使用する場合
export OPENAI_API_KEY=your-api-key-here

# またはローカルLLMを使用する場合
# Ollamaのインストールと起動
ollama pull llama3
ollama serve
```

## 日常の開発ワークフロー

### ブランチ管理

#### 機能開発の場合
```bash
# 機能ブランチの作成
git checkout -b feature/your-feature-name

# 開発作業
# ... コード変更 ...

# コミット
git add .
git commit -m "feat: 機能の説明"

# プッシュ
git push origin feature/your-feature-name
```

#### バグ修正の場合
```bash
# バグ修正ブランチの作成
git checkout -b fix/issue-number-description

# 修正作業
# ... コード変更 ...

# コミット
git add .
git commit -m "fix: バグの説明 (issue #123)"
```

### コード変更の流れ

#### 1. 作業開始前の準備
```bash
# 最新のmainブランチを取得
git checkout main
git pull origin main

# 作業ブランチを作成
git checkout -b feature/your-feature
```

#### 2. コード変更
```bash
# コードを変更
vim docgen/generators/your_module.py

# フォーマット適用
uv run ruff format .

# リンター実行
uv run ruff check . --fix
```

#### 3. テスト実行
```bash
# 関連するテストを実行
uv run pytest tests/test_generators/ -v

# カバレッジ付きで実行
uv run pytest tests/ --cov=docgen --cov-report=html
```

#### 4. コミット
```bash
# 変更を確認
git status
git diff

# ステージング
git add .

# コミット（Conventional Commits形式）
git commit -m "feat: 新機能の追加

- 機能Aを実装
- 機能Bを改善
- テストを追加"
```

#### 5. プッシュとPR作成
```bash
# プッシュ
git push origin feature/your-feature

# GitHubでPRを作成
# タイトル: "feat: 新機能の追加"
# 説明: 変更内容、テスト結果、関連Issueを記載
```

## コード品質管理

### 自動品質チェック

#### コミット前のチェック
```bash
# 全品質チェックを実行
./scripts/run_pipeline.sh

# または個別に実行
./scripts/run_lint.sh    # リンター
./scripts/run_format.sh  # フォーマッター
./scripts/run_tests.sh   # テスト
```

#### 継続的インテグレーション
GitHub Actionsで以下のチェックが自動実行されます：
- Python構文チェック
- リンター（ruff）
- テスト実行（pytest）
- カバレッジレポート

### コード品質基準

#### リンター設定（ruff）
- **対象ルール**: E, W, F, I, B, C4, UP
- **行長**: 100文字
- **Pythonバージョン**: 3.12以上

#### テストカバレッジ
- **目標**: 80%以上
- **主要コンポーネント**: 90%以上

#### コミットメッセージ
[Conventional Commits](https://www.conventionalcommits.org/)形式を使用：
```
type(scope): description

[body]

[footer]
```

**type**: feat, fix, docs, style, refactor, test, chore
**scope**: 変更対象のモジュール名（任意）

## テスト実行

### 基本的なテスト実行

#### 全テスト実行
```bash
uv run pytest tests/
```

#### 特定のテスト実行
```bash
# ジェネレーターのテストのみ
uv run pytest tests/test_generators/ -v

# 特定のテストクラス
uv run pytest tests/test_generators/test_agents_generator.py::TestAgentsGenerator -v

# 特定のテストメソッド
uv run pytest tests/test_generators/test_agents_generator.py::TestAgentsGenerator::test_initialization -v
```

#### カバレッジレポート付き実行
```bash
# HTMLレポート生成
uv run pytest tests/ --cov=docgen --cov-report=html

# レポート閲覧
open htmlcov/index.html
```

### テストの種類

#### 1. ユニットテスト
```bash
# 特定のモジュールのテスト
uv run pytest tests/test_config_manager.py -v
```

#### 2. 統合テスト
```bash
# エンド-to-エンドテスト
uv run pytest tests/test_integration.py -v
```

#### 3. エッジケーステスト
```bash
# 異常系テスト
uv run pytest tests/test_edge_cases.py -v
```

### テスト作成ガイドライン

#### テストファイルの構造
```python
import pytest
from docgen.your_module import YourClass
from tests.test_utils import assert_file_exists_and_not_empty

class TestYourClass:
    """YourClassのテストクラス"""

    def test_initialization(self, your_fixture):
        """初期化テスト"""
        instance = YourClass(param)
        assert instance.attribute == expected_value

    def test_main_functionality(self, your_fixture):
        """主要機能のテスト"""
        result = instance.process()
        assert result == expected_result
```

#### フィクスチャの使用
conftest.pyで定義された共通フィクスチャを使用：
- `temp_project`: 一時プロジェクトディレクトリ
- `python_project`: Pythonプロジェクト構造
- `agents_generator`: AgentsGeneratorインスタンス
- `config_manager`: ConfigManagerインスタンス

## リリース手順

### バージョン管理

#### バージョン番号の更新
```bash
# pyproject.tomlのversionを更新
vim pyproject.toml

# 例: version = "0.1.0" → version = "0.1.1"
```

#### リリースノートの作成
```bash
# RELEASE.mdを更新
vim RELEASE.md

# 変更内容を記載
```

### リリース実行

#### 1. リリースブランチの作成
```bash
git checkout -b release/v0.1.1
```

#### 2. 最終テスト
```bash
# 全テスト実行
uv run pytest tests/ --cov=docgen

# パイプライン実行
./scripts/run_pipeline.sh
```

#### 3. タグ付けとリリース
```bash
# コミット
git add .
git commit -m "release: v0.1.1"

# タグ付け
git tag -a v0.1.1 -m "Release version 0.1.1"

# プッシュ
git push origin release/v0.1.1
git push origin v0.1.1
```

#### 4. GitHub Release作成
GitHub UIで以下の手順：
1. Releasesページを開く
2. "Create a new release"をクリック
3. Tag version: v0.1.1
4. Release title: Release v0.1.1
5. Description: リリースノートを記載
6. "Publish release"をクリック

### パッケージ公開

#### PyPIへの公開
```bash
# ビルド
uv build

# 公開
uv publish
```

## トラブルシューティング

### よくある問題と解決法

#### 1. インポートエラー
```bash
# PYTHONPATHの設定確認
export PYTHONPATH=/path/to/agents-docs-sync:$PYTHONPATH

# 依存関係の再インストール
uv sync --reinstall
```

#### 2. テスト実行エラー
```bash
# キャッシュクリア
uv run pytest --cache-clear

# 詳細ログ表示
uv run pytest -v -s --tb=long
```

#### 3. カバレッジが低い
```bash
# カバレッジレポート確認
uv run pytest --cov=docgen --cov-report=html
open htmlcov/index.html

# 未カバー行の特定
uv run pytest --cov=docgen --cov-report=term-missing
```

#### 4. リンターエラー
```bash
# 自動修正
uv run ruff check . --fix

# 設定確認
uv run ruff check . --show-settings
```

#### 5. LLM API接続エラー
```bash
# APIキーの確認
echo $OPENAI_API_KEY

# ネットワーク接続確認
curl -I https://api.openai.com/v1/models
```

### デバッグ手順

#### ログレベルの変更
```python
# デバッグログ有効化
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 設定ファイルの検証
```bash
# YAML構文チェック
python -c "import yaml; yaml.safe_load(open('docgen/config.toml'))"
```

#### 依存関係の確認
```bash
# インストール済みパッケージ確認
uv pip list

# 特定のバージョン確認
uv run python -c "import pyyaml; print(pyyaml.__version__)"
```

## 貢献ガイドライン

### Issueの作成

#### バグ報告
- **タイトル**: `[Bug] 簡潔な説明`
- **内容**:
  - 再現手順
  - 期待される動作
  - 実際の動作
  - 環境情報（Pythonバージョン、OSなど）

#### 機能リクエスト
- **タイトル**: `[Feature] 機能名`
- **内容**:
  - 機能の詳細説明
  - 使用例
  - 利点

### プルリクエストの作成

#### 1. 事前準備
- Issueを作成または既存Issueを確認
- ブランチ名: `feature/`, `fix/`, `docs/`, `refactor/` のいずれか

#### 2. 変更内容
- 1つのPRで1つの機能/修正に集中
- コミットメッセージは明確に
- テストを追加/更新

#### 3. PRテンプレート
```markdown
## 概要
何を実装/修正したか

## 変更内容
- [ ] 機能Aを実装
- [ ] テストを追加
- [ ] ドキュメントを更新

## テスト
- [ ] 全テスト通過
- [ ] カバレッジ80%以上維持

## 関連Issue
#123
```

#### 4. レビュー対応
- レビューコメントに迅速に対応
- 必要に応じてコミットを修正
- マージ前に全チェックを通過

### コードレビューの観点

#### レビュアーのチェック項目
- [ ] コードの品質（可読性、保守性）
- [ ] テストの充実度
- [ ] ドキュメントの更新
- [ ] パフォーマンスへの影響
- [ ] セキュリティ上の懸念

#### レビュアーの承認基準
- [ ] 全自動チェック（CI/CD）通過
- [ ] テストカバレッジ80%以上
- [ ] コードレビューの承認
- [ ] 機能テストの確認

## 定期メンテナンス

### 週次タスク
- [ ] 依存関係の更新確認
- [ ] セキュリティ脆弱性のチェック
- [ ] GitHub Issuesの整理

### 月次タスク
- [ ] パフォーマンステスト
- [ ] ドキュメントの更新
- [ ] リリース計画の策定

### 四半期タスク
- [ ] 大規模リファクタリング
- [ ] アーキテクチャの見直し
- [ ] 技術スタックの更新

---

**最終更新**: 2025-11-20
**バージョン**: 0.0.1</content>
<parameter name="filePath">PROJECT_MANAGEMENT_GUIDE.md
