# リリース手順

このドキュメントでは、agents-docs-syncのリリース手順を説明します。

## リリース方法

### 方法1: タグを使用した自動リリース（推奨）

1. **バージョン番号の更新**
   ```bash
   # pyproject.tomlのversionを更新
   # 例: version = "0.0.2"
   ```

2. **変更をコミット**
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 0.0.2"
   ```

3. **タグを作成してプッシュ**
   ```bash
   git tag -a v0.0.2 -m "Release version 0.0.2"
   git push origin v0.0.2
   ```

4. **GitHub Actionsが自動的にリリースを作成**
   - `.github/workflows/release.yml`が自動実行されます
   - ビルド、パッケージング、GitHubリリースの作成が行われます

### 方法2: リリーススクリプトを使用（簡単）

リリーススクリプトを使用すると、対話形式でリリースを実行できます：

```bash
# リリーススクリプトを実行
./scripts/release.sh
```

スクリプトは以下の処理を自動的に行います：
1. 現在のバージョンを表示
2. 新しいバージョン番号の入力を求める
3. `pyproject.toml`のバージョンを更新
4. 変更をコミット（オプション）
5. タグを作成してプッシュ（オプション）

### 方法3: 自動リリース（pre-pushフック）

プッシュ時にバージョン番号の変更を検出して、自動的にリリースタグを作成できます。

**セットアップ:**

1. **pre-pushフックをインストール**
   ```bash
   ./setup.sh
   ```

2. **環境変数を設定して有効化**
   ```bash
   export AUTO_RELEASE_ENABLED=1
   ```

3. **バージョン番号を更新してプッシュ**
   ```bash
   # pyproject.tomlのversionを更新
   git add pyproject.toml
   git commit -m "Bump version to 0.0.2"
   git push  # プッシュ時に自動的にタグ作成を提案
   ```

**注意:** この方法は対話形式です。バージョンが変更された場合、プッシュ時に確認を求められます。

### 方法4: 手動リリース（GitHub Actions UI）

1. GitHubリポジトリの「Actions」タブに移動
2. 「Release」ワークフローを選択
3. 「Run workflow」をクリック
4. バージョン番号を入力（例: `0.0.2`）
5. 「Run workflow」をクリック

## PyPIへの公開（オプション）

PyPIに公開する場合は、以下の手順を実行してください：

1. **PyPI APIトークンの取得**
   - https://pypi.org/manage/account/token/ にアクセス
   - APIトークンを作成

2. **GitHub Secretsに追加**
   - リポジトリの「Settings」→「Secrets and variables」→「Actions」
   - 「New repository secret」をクリック
   - Name: `PYPI_API_TOKEN`
   - Value: PyPI APIトークンを貼り付け
   - 「Add secret」をクリック

3. **ワークフローの有効化**
   - `.github/workflows/release.yml`を編集
   - `Publish to PyPI`ステップの`if: false`を`if: true`に変更

4. **リリースを実行**
   - 上記の「方法1」または「方法2」でリリースを実行
   - PyPIへの公開が自動的に行われます

## ローカルでのビルドとテスト

リリース前に、ローカルでビルドとテストを実行することを推奨します：

**注意:** このプロジェクトは`hatchling`をビルドバックエンドとして使用しています。

### 方法1: uvを使用（推奨）

```bash
# 開発依存関係のインストール（buildツールを含む）
uv sync --group dev

# パッケージのビルド
uv build

# ビルド結果の確認
ls -la dist/

# テストインストール
pip install dist/agents_docs_sync-*.whl

# 動作確認
agents-docs-sync --help
```

### 方法2: pipを使用

```bash
# ビルドツールのインストール
pip install build

# パッケージのビルド
python -m build

# ビルド結果の確認
ls -la dist/

# テストインストール
pip install dist/agents_docs_sync-*.whl

# 動作確認
agents-docs-sync --help
```

### 方法3: hatchを使用

```bash
# hatchのインストール
pip install hatch

# パッケージのビルド
hatch build

# ビルド結果の確認
ls -la dist/

# テストインストール
pip install dist/agents_docs_sync-*.whl

# 動作確認
agents-docs-sync --help
```

## リリースノート

GitHub Actionsは自動的にリリースノートを生成しますが、手動で編集することもできます。

リリースノートには以下を含めることを推奨します：
- 新機能
- バグ修正
- 破壊的変更（あれば）
- 依存関係の更新

## バージョン番号の規則

[Semantic Versioning](https://semver.org/)に従います：
- **MAJOR**: 互換性のない変更
- **MINOR**: 後方互換性のある新機能
- **PATCH**: バグ修正

例: `0.1.0` → `0.1.1` (パッチ), `0.1.0` → `0.2.0` (マイナー), `0.1.0` → `1.0.0` (メジャー)

## トラブルシューティング

### リリースが作成されない

- タグが正しい形式か確認（`v`で始まる必要がある）
- GitHub Actionsのログを確認
- ワークフローファイルの構文エラーを確認

### PyPIへの公開が失敗する

- `PYPI_API_TOKEN`が正しく設定されているか確認
- トークンに適切な権限があるか確認
- バージョン番号が既に存在しないか確認

### CursorでGitフックが実行されない

CursorでGit操作を行う場合、一部のGitフック（特に`pre-push`）が実行されないことがあります。

**原因:**
- CursorはGit操作を最適化するため、一部のフックをスキップする場合がある
- 対話的なフック（`read`コマンドを含む）が正常に動作しない場合がある

**解決策:**

1. **ターミナルから直接Gitコマンドを実行（推奨）**
   ```bash
   # Cursorの統合ターミナルまたは外部ターミナルで実行
   git push
   ```

2. **リリーススクリプトを使用**
   ```bash
   # フックに依存せず、直接スクリプトを実行
   ./scripts/release.sh
   ```

3. **フックを再インストール**
   ```bash
   ./scripts/install_hooks.sh
   ```

詳細は `docs/CURSOR_GIT_HOOKS.md` を参照してください。

