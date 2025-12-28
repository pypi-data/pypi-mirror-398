# Configuration Guide

agents-docs-syncの設定ファイル完全ガイド

## 目次

- [設定ファイルの場所](#設定ファイルの場所)
- [設定セクション](#設定セクション)
  - [言語設定](#言語設定)
  - [出力設定](#出力設定)
  - [生成設定](#生成設定)
  - [AGENTS設定](#agents設定)
  - [RAG設定](#rag設定)
  - [除外設定](#除外設定)
- [Hooks設定](#hooks設定)
- [移行ガイド](#移行ガイド)

## 設定ファイルの場所

プロジェクトルートの`docgen/config.toml`に設定ファイルを配置します。

初期化コマンドでサンプルファイルが作成されます：
```bash
agents_docs_sync init
```

## 設定セクション

### 言語設定

プロジェクトで使用されるプログラミング言語を制御します。

```toml
[languages]
auto_detect = true          # 自動検出を有効化
preferred = ["python", "javascript"]  # 優先言語リスト
```

**オプション:**
- `auto_detect`: `true`/`false` - コードベースから言語を自動検出
- `preferred`: 配列 - 複数言語が検出された場合の優先順位

**ベストプラクティス:**
- モノリポジトリでは`preferred`を使用して主要言語を指定
- 単一言語プロジェクトでは`auto_detect = true`のみでOK

### 出力設定

生成されるドキュメントのパスを設定します。

```toml
[output]
api_doc = "docs/api.md"      # APIドキュメントパス
readme = "README.md"          # READMEファイルパス
agents_doc = "AGENTS.md"      # AGENTSドキュメントパス
```

**注意:**
- すべてのパスはプロジェクトルートからの相対パス
- ディレクトリは自動作成されます

### 生成設定

ドキュメント生成の動作を制御します。

```toml
[generation]
update_readme = true
generate_api_doc = true
generate_agents_doc = true
agents_mode = "hybrid"              # "template", "llm", "hybrid"
readme_mode = "hybrid"
preserve_manual_sections = true
use_outlines = false                # 実験的機能
```

**生成モード:**
- `"template"`: テンプレートベース（高速、LLM不要）
- `"llm"`: LLM完全生成（高品質、API必要）
- `"hybrid"`: テンプレート+LLM補完（推奨）

**manual sections:**
```markdown
<!-- MANUAL_START:custom_section -->
この部分は自動生成時も保持されます
<!-- MANUAL_END:custom_section -->
```

### キャッシュ設定

パフォーマンス最適化のためのキャッシュ設定。

```toml
[cache]
enabled = true
```

変更されていないファイルの再解析をスキップし、生成速度を向上させます。

### AGENTS設定

LLM統合とAGENTS.md生成を設定します。

#### LLMモード

```toml
[agents]
llm_mode = "both"  # "api", "local", "both"
```

- `"api"`: OpenAI/Anthropic などのAPI使用
- `"local"`: Ollama/LM Studioなどのローカルモデル
- `"both"`: 両方を使用（APIがフォールバック）

#### API設定

```toml
[agents.api]
provider = "openai"           # "openai", "anthropic"
model = "gpt-4o"
api_key_env = "OPENAI_API_KEY"
timeout = 180
max_retries = 3
retry_delay = 1.0
```

**環境変数:**
```bash
export OPENAI_API_KEY="your-api-key"
```

**サポートされるプロバイダー:**
- `openai`: GPT-4, GPT-3.5-turbo
- `anthropic`: Claude 3.5 Sonnet, Claude 3 Opus

#### ローカルLLM設定

```toml
[agents.local]
provider = "ollama"
model = "llama3"
base_url = "http://localhost:11434"
timeout = 180
```

**Ollama使用例:**
```bash
# Ollamaインストール
curl https://ollama.ai/install.sh | sh

# モデルダウンロード
ollama pull llama3

# サーバー起動（バックグラウンド実行中）
ollama serve
```

#### コーディング規約

```toml
[agents.coding_standards]
auto_detect = true
```

手動指定も可能：
```toml
[agents.coding_standards]
auto_detect = false
style_guide = "PEP 8"
formatter = "black"
linter = "ruff"
```

### RAG設定

Retrieval-Augmented Generation（実験的機能）

```toml
[rag]
enabled = true
auto_build_index = true
```

#### 埋め込みモデル

```toml
[rag.embedding]
model = "all-MiniLM-L6-v2"    # 軽量・高速
device = "cpu"                 # "cpu" or "cuda"
```

**推奨モデル:**
- `all-MiniLM-L6-v2`: 軽量（384次元）、高速
- `all-mpnet-base-v2`: 高精度（768次元）、やや重い

#### インデックス設定

```toml
[rag.index]
type = "hnswlib"        # "hnswlib" or "faiss"
ef_construction = 200
M = 16
```

**パラメータ調整:**
- `ef_construction`: 構築時の探索範囲（大きいほど精度向上、遅くなる）
- `M`: グラフ接続数（大きいほど精度向上、メモリ増加）

#### 検索設定

```toml
[rag.retrieval]
top_k = 6
score_threshold = 0.3
```

- `top_k`: 取得するチャンク数
- `score_threshold`: 類似度閾値（0.0-1.0）

#### 除外設定

機密情報を保護するための除外パターン：

```toml
[rag.exclude_patterns]
patterns = [
    '.*\.env$',
    'secrets/.*',
    '.*_SECRET.*',
    '.*API_KEY.*',
]

[rag.exclude_files]
files = ["README.md", "AGENTS.md"]
```

### 除外設定

解析から除外するディレクトリとファイル：

```toml
[exclude]
directories = [
    ".venv",
    "node_modules",
    "__pycache__",
    ".git",
]

patterns = [
    "*.pyc",
    "*.log",
]
```

## Hooks設定

Git hooksの設定は`docgen/hooks.toml`で管理します。

### Pre-commit Hook

コミット前の自動タスク実行：

```toml
[hooks.pre-commit]
enabled = true

[[hooks.pre-commit.tasks]]
name = "generate_docs"
enabled = true
continue_on_error = false

[[hooks.pre-commit.tasks]]
name = "stage_changes"
enabled = true
params = { files = ["README.md", "AGENTS.md"] }
```

**利用可能なタスク:**
- `run_tests`: テスト実行
- `generate_rag`: RAGインデックス構築
- `generate_docs`: ドキュメント生成
- `stage_changes`: 生成ファイルをステージング

### Commit-msg Hook

```toml
[hooks.commit-msg]
enabled = true

[[hooks.commit-msg.tasks]]
name = "generate_commit_message"
enabled = true
params = { only_if_empty = true }
```

空のコミットメッセージを自動生成します。

### Hooks インストール

```bash
agents_docs_sync hook install
```

## 移行ガイド

### YAML から TOML への移行

既存の`config.yaml`がある場合：

1. **バックアップ作成**
   ```bash
   cp docgen/config.yaml docgen/config.yaml.backup
   ```

2. **新しいTOML設定を生成**
   ```bash
   agents_docs_sync init
   ```

3. **設定を手動移行**

   YAML:
   ```yaml
   languages:
     auto_detect: true
     preferred:
       - python
       - javascript
   ```

   TOML:
   ```toml
   [languages]
   auto_detect = true
   preferred = ["python", "javascript"]
   ```

4. **検証**
   ```bash
   agents_docs_sync
   ```

### 重要な構文の違い

**配列:**
```yaml
# YAML
items:
  - item1
  - item2
```
```toml
# TOML
items = ["item1", "item2"]
```

**テーブル配列:**
```yaml
# YAML
tasks:
  - name: task1
    enabled: true
  - name: task2
    enabled: false
```
```toml
# TOML
[[tasks]]
name = "task1"
enabled = true

[[tasks]]
name = "task2"
enabled = false
```

**複数行文字列:**
```yaml
# YAML
text: |
  line 1
  line 2
```
```toml
# TOML
text = """
line 1
line 2
"""
```

## トラブルシューティング

### TOMLパースエラー

**エラー:** `TOMLDecodeError: Invalid TOML file`

**解決策:**
- TOMLシンタックスを確認（オンライン検証ツール: https://www.toml-lint.com/）
- 特殊文字（`#`, `[`, `]`）が文字列内にある場合は引用符で囲む

### 設定が反映されない

**確認項目:**
1. ファイルパス: `docgen/config.toml`
2. ファイル形式: `.toml`拡張子
3. キャッシュクリア: プロジェクトルートの`.cache`ディレクトリ削除

### LLM接続エラー

**API使用時:**
```bash
# 環境変数を確認
echo $OPENAI_API_KEY
```

**ローカルLLM使用時:**
```bash
# Ollamaサーバー起動確認
curl http://localhost:11434/api/tags
```

## ベストプラクティス

1. **バージョン管理**: `config.toml`をGitに含める（`.env`は除外）
2. **チーム共有**: プロジェクト標準設定を`config.toml.sample`として共有
3. **環境別設定**: 環境変数でAPI keyなどを管理
4. **段階的導入**: まず`template`モードで動作確認、その後`hybrid`に移行

## 関連リンク

- [TOML仕様](https://toml.io/)
- [agents-docs-sync README](../README.md)
- [AGENTS.md](../AGENTS.md)
