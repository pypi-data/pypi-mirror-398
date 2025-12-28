# RAG関連度検出ロジックの説明

## 現在の実装

### 1. クエリ生成

**場所:** `docgen/generators/readme_generator.py`, `docgen/generators/agents_generator.py`

**現在のクエリ形式:**
```python
query = f"{prompt_name} for {self.project_root.name}"
# 例: "project overview for Locus"
```

**問題点:**
- クエリが非常にシンプルで、プロジェクトの具体的な内容を含んでいない
- プロジェクトの技術スタック、主要機能、アーキテクチャなどの情報が含まれていない
- 自然言語クエリとコードチャンクの意味的関連性が低い可能性がある

### 2. チャンク化

**場所:** `docgen/rag/chunker.py`, `docgen/rag/strategies/code_strategy.py`

**チャンクの内容:**
- 関数定義、クラス定義、インターフェース定義のコードそのもの
- コメントやdocstringは含まれるが、コードが主

**問題点:**
- コードそのものがチャンク化されているため、自然言語クエリとの関連性が低い
- 関数名やクラス名だけでは、プロジェクトの全体像を把握しにくい

### 3. 埋め込み生成

**場所:** `docgen/rag/embedder.py`

**使用モデル:**
- デフォルト: `all-MiniLM-L6-v2` (384次元)
- sentence-transformersを使用

**処理:**
1. クエリテキストを埋め込みベクトルに変換
2. 各チャンクのテキストを埋め込みベクトルに変換
3. キャッシュ機能あり（同じテキストは再計算しない）

### 4. 類似度検索

**場所:** `docgen/rag/indexer.py`

**検索アルゴリズム:**
- HNSW (Hierarchical Navigable Small World) を使用
- コサイン距離で類似度を計算
- 距離を類似度スコアに変換: `similarity = 1.0 - distance`

**検索プロセス:**
```python
# 1. クエリを埋め込みベクトルに変換
query_embedding = embedder.embed_text(query)

# 2. インデックスから類似ベクトルを検索
labels, distances = index.knn_query(query_embedding, k=k)

# 3. 距離を類似度スコアに変換
similarity = 1.0 - distance
```

### 5. フィルタリング

**場所:** `docgen/rag/retriever.py`

**現在のロジック:**
1. **初期フィルタリング**: スコアが閾値（デフォルト: 0.3）以上のチャンクを取得
2. **動的閾値調整**: 結果が少ない場合（top_kの20%未満）、閾値を自動的に下げる
   - 新しい閾値 = `min(元の閾値, max(0.15, 最低スコア * 0.8))`

**設定:**
```toml
[rag.retrieval]
top_k = 24
score_threshold = 0.5  # 設定ファイルでは0.5だが、コードのデフォルトは0.3
```

## 問題点の分析

### 1. クエリとチャンクの意味的ギャップ

**問題:**
- クエリ: "project overview for Locus"（自然言語、抽象的）
- チャンク: コードそのもの（関数定義、クラス定義など）

**影響:**
- 埋め込みモデルがコードと自然言語の関連性を正しく捉えられない
- スコアが全体的に低くなる

### 2. チャンクの品質

**問題:**
- コードのみがチャンク化されている
- プロジェクトの説明やドキュメントが含まれていない

**影響:**
- プロジェクトの全体像を把握するための情報が不足
- 自然言語クエリとの関連性が低い

### 3. 閾値の設定

**問題:**
- 設定ファイルでは`score_threshold = 0.5`だが、コードのデフォルトは`0.3`
- 閾値が高すぎると、関連するチャンクも除外される

**影響:**
- 165個のチャンクがあるのに、1個しか取得できない

## 改善案

### 1. クエリ生成の改善

**提案:**
```python
# 現在
query = f"project overview for {self.project_root.name}"

# 改善案
query = f"""
Project: {self.project_root.name}
Languages: {', '.join(self.languages)}
Main features: {extract_main_features(project_info)}
Architecture: {extract_architecture_summary(project_info)}
What is this project about? What are the main components and functionality?
"""
```

**効果:**
- プロジェクトの具体的な情報を含む
- より詳細なクエリで、関連チャンクを特定しやすくなる

### 2. チャンクの改善

**提案:**
- チャンクにメタデータを追加（関数名、クラス名、ファイルパスなど）
- チャンクのテキストに説明を追加（"This function does X"など）
- プロジェクトのREADMEやドキュメントもチャンク化

**効果:**
- より意味的な情報を含むチャンク
- 自然言語クエリとの関連性が向上

### 3. マルチクエリ検索

**提案:**
- 複数のクエリを生成して検索
- 結果をマージして重複を除去

**効果:**
- より多様な関連チャンクを取得
- プロジェクトの異なる側面をカバー

### 4. 再ランキング

**提案:**
- Cross-encoderモデルを使用して再ランキング
- より正確な関連度スコアを計算

**効果:**
- 関連度の精度が向上
- より適切なチャンクを取得

## 現在の実装の流れ

```
1. クエリ生成
   "project overview for Locus"
   ↓
2. 埋め込み生成
   Embedder.embed_text(query) → [384次元のベクトル]
   ↓
3. ベクトル検索
   VectorIndexer.search(query_embedding, k=24)
   → hnswlibでコサイン距離を計算
   → 距離を類似度に変換 (1 - distance)
   ↓
4. フィルタリング
   score >= 0.3 のチャンクを取得
   → 結果が少ない場合は閾値を自動調整
   ↓
5. コンテキスト生成
   format_context(chunks) → フォーマット済みテキスト
```

## 関連度スコアの意味

- **1.0**: 完全に一致（通常は発生しない）
- **0.7-0.9**: 非常に高い関連性
- **0.5-0.7**: 高い関連性
- **0.3-0.5**: 中程度の関連性
- **0.0-0.3**: 低い関連性

**現在の問題:**
- コードチャンクと自然言語クエリの関連性が低いため、スコアが全体的に低くなる
- 閾値0.3でも、多くのチャンクが除外される可能性がある

## 推奨される改善

1. **即座に実施可能:**
   - クエリ生成の改善（プロジェクト情報を含める）
   - 閾値の調整（0.3 → 0.2 または 0.15）
   - スコア統計情報のログ出力（既に実装済み）

2. **中期的な改善:**
   - チャンクの品質向上（メタデータ追加、説明追加）
   - マルチクエリ検索の実装

3. **長期的な改善:**
   - 再ランキングの実装（Cross-encoder）
   - コード専用の埋め込みモデルの使用

