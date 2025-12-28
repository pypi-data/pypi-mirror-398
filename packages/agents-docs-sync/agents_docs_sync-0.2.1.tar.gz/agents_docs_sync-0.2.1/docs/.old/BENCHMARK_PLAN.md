# ベンチマークツール開発計画

## タスク分析

### 主要なタスク
プロセスのボトルネックを特定するためのベンチマークツールを開発し、各処理の実行時間、メモリ使用量、CPU使用率を測定できるようにする。

### 技術スタック
- **言語**: Python 3.12+
- **既存依存関係**:
  - `pydantic>=2.0.0` (データモデル用)
  - `pyyaml>=6.0.3` (設定ファイル用)
  - `pytest>=9.0.1` (テスト用)
- **追加が必要な依存関係**:
  - `psutil>=5.9.0` (システムリソース監視用)
  - `memory-profiler>=0.61.0` (メモリプロファイリング用、オプション)
  - `py-spy>=0.3.14` (CPUプロファイリング用、オプション)

### 重要な要件と制約
1. **非侵入性**: 既存のコードに最小限の変更で統合可能
2. **柔軟性**: 特定の処理のみを測定可能
3. **詳細な測定**: 実行時間、メモリ、CPU使用率を記録
4. **レポート生成**: 測定結果を読みやすい形式で出力
5. **CLI統合**: 既存のCLIコマンド体系に統合
6. **設定可能**: 測定対象や出力形式を設定可能

### 潜在的な課題
1. **パフォーマンスオーバーヘッド**: ベンチマークツール自体が処理を遅くしないようにする
2. **非同期処理の測定**: LLM API呼び出しなどの非同期処理の正確な測定
3. **メモリプロファイリングの精度**: ガベージコレクションの影響
4. **並列処理の測定**: 複数の処理が並列実行される場合の測定

### タスク実行のための具体的なステップ

#### フェーズ1: コアベンチマーク機能の実装
1. **ベンチマークデコレータ/コンテキストマネージャーの作成**
   - 関数やコードブロックの実行時間を測定
   - メモリ使用量の追跡
   - CPU使用率の監視
   - 測定結果のデータ構造定義

2. **ベンチマーク結果のデータモデル定義**
   - Pydanticモデルで測定結果を構造化
   - 階層的な測定結果（親処理と子処理）
   - 統計情報（平均、最小、最大、標準偏差）

3. **ベンチマークレコーダーの実装**
   - 測定結果の収集と保存
   - 結果の集計と統計計算
   - 結果のエクスポート（JSON、CSV、Markdown）

#### フェーズ2: 主要処理への統合
4. **ドキュメント生成処理の測定ポイント特定**
   - 言語検出処理
   - 各ジェネレーター（API、README、AGENTS.md等）
   - ファイルI/O操作
   - パーサー処理

5. **RAG処理の測定ポイント特定**
   - インデックス構築
   - 埋め込み生成
   - ベクトル検索
   - チャンキング処理

6. **LLM処理の測定ポイント特定**
   - API呼び出し時間
   - トークン使用量
   - レート制限待機時間
   - エラーハンドリング時間

#### フェーズ3: CLI統合とレポート生成
7. **CLIコマンドの実装**
   - `benchmark` サブコマンドの追加
   - 測定対象の選択オプション
   - 出力形式の選択オプション
   - 比較モード（複数実行の比較）

8. **レポート生成機能**
   - Markdown形式のレポート
   - グラフ生成（matplotlibまたは別ツール）
   - ボトルネックの自動検出とハイライト
   - 改善提案の生成

#### フェーズ4: 高度な機能
9. **プロファイリング統合**
   - cProfileとの統合
   - ホットスポットの特定
   - 関数呼び出し回数のカウント

10. **比較機能**
    - 複数のベンチマーク実行結果の比較
    - パフォーマンス回帰の検出
    - トレンド分析

### 実行順序
1. フェーズ1: コア機能の実装（基盤となる）
2. フェーズ2: 主要処理への統合（実際の測定）
3. フェーズ3: CLI統合とレポート生成（使いやすさ）
4. フェーズ4: 高度な機能（オプション）

### 必要なツールとリソース
- **開発ツール**:
  - Python開発環境
  - 既存のテストスイート
- **ライブラリ**:
  - `psutil`: システムリソース監視
  - `pydantic`: データモデル
  - `pyyaml`: 設定ファイル
- **オプションライブラリ**:
  - `memory-profiler`: 詳細なメモリプロファイリング
  - `matplotlib`: グラフ生成
  - `pandas`: データ分析

## 実装計画の詳細

### ディレクトリ構造
```
docgen/
├── benchmark/
│   ├── __init__.py
│   ├── core.py              # コアベンチマーク機能（デコレータ、コンテキストマネージャー）
│   ├── recorder.py           # ベンチマーク結果の記録と集計
│   ├── models.py             # ベンチマーク結果のデータモデル
│   ├── reporter.py           # レポート生成
│   ├── profiler.py           # プロファイリング統合
│   └── utils.py              # ユーティリティ関数
├── cli/
│   └── commands/
│       └── benchmark.py      # benchmarkコマンドの実装
└── ...
```

### 主要なクラスと関数

#### 1. `BenchmarkContext` (コンテキストマネージャー)
```python
class BenchmarkContext:
    """ベンチマーク測定用のコンテキストマネージャー"""
    def __enter__(self) -> "BenchmarkContext":
        # 測定開始
    def __exit__(self, ...) -> None:
        # 測定終了と結果記録
```

#### 2. `benchmark` (デコレータ)
```python
def benchmark(name: str, enabled: bool = True):
    """関数の実行時間を測定するデコレータ"""
```

#### 3. `BenchmarkRecorder`
```python
class BenchmarkRecorder:
    """ベンチマーク結果の記録と集計を行うクラス"""
    def record(self, result: BenchmarkResult) -> None:
    def get_summary(self) -> BenchmarkSummary:
    def export(self, format: str, path: Path) -> None:
```

#### 4. `BenchmarkResult` (Pydanticモデル)
```python
class BenchmarkResult(BaseModel):
    """ベンチマーク測定結果"""
    name: str
    duration: float
    memory_peak: int
    memory_delta: int
    cpu_percent: float
    timestamp: datetime
    children: list["BenchmarkResult"] = []
```

#### 5. `BenchmarkReporter`
```python
class BenchmarkReporter:
    """ベンチマーク結果のレポート生成"""
    def generate_markdown(self, results: list[BenchmarkResult]) -> str:
    def generate_json(self, results: list[BenchmarkResult]) -> dict:
    def detect_bottlenecks(self, results: list[BenchmarkResult]) -> list[str]:
```

### 測定対象の処理

#### 高優先度（主要なボトルネック候補）
1. **言語検出処理** (`LanguageDetector.detect_languages`)
2. **ドキュメント生成全体** (`DocumentGenerator.generate_documents`)
3. **APIドキュメント生成** (`APIGenerator.generate`)
4. **README生成** (`ReadmeGenerator.generate`)
5. **RAGインデックス構築** (`VectorIndexer.build`)
6. **埋め込み生成** (`Embedder.embed`)
7. **LLM API呼び出し** (`LLMService.generate`)

#### 中優先度
8. **ファイル読み込み/書き込み**
9. **パーサー処理** (Python/JSパーサー)
10. **設定ファイル読み込み**

#### 低優先度（詳細分析が必要な場合）
11. **個別のコレクター処理**
12. **テンプレートレンダリング**
13. **キャッシュ操作**

### CLIコマンド仕様

```bash
# 基本的な使用
agents_docs_sync benchmark

# 特定の処理のみ測定
agents_docs_sync benchmark --target generate --target rag

# 出力形式の指定
agents_docs_sync benchmark --format json --output results.json

# 詳細モード
agents_docs_sync benchmark --verbose

# 比較モード（複数実行の比較）
agents_docs_sync benchmark --compare baseline.json current.json
```

### 出力例

#### Markdownレポート
```markdown
# ベンチマーク結果

## 実行概要
- 実行日時: 2025-12-12 15:00:00
- 総実行時間: 45.23秒
- ピークメモリ使用量: 512 MB

## 処理別実行時間

| 処理名 | 実行時間 | メモリ使用量 | CPU使用率 | ボトルネック |
|--------|----------|--------------|-----------|--------------|
| 言語検出 | 2.34秒 | 45 MB | 15% | |
| APIドキュメント生成 | 25.67秒 | 234 MB | 45% | ⚠️ |
| RAGインデックス構築 | 12.45秒 | 189 MB | 60% | ⚠️ |
| README生成 | 4.77秒 | 67 MB | 20% | |

## ボトルネック分析

1. **APIドキュメント生成** (25.67秒, 45%)
   - 主な要因: LLM API呼び出しの待機時間
   - 改善提案: バッチ処理または並列化の検討

2. **RAGインデックス構築** (12.45秒, 60%)
   - 主な要因: 埋め込み生成の処理時間
   - 改善提案: キャッシュの活用
```

### 実装の優先順位

1. **必須機能** (MVP)
   - 基本的な実行時間測定
   - メモリ使用量の追跡
   - シンプルなMarkdownレポート生成
   - CLIコマンドの基本実装

2. **重要機能**
   - CPU使用率の監視
   - 階層的な測定結果
   - JSON/CSVエクスポート
   - ボトルネックの自動検出

3. **拡張機能**
   - グラフ生成
   - 比較機能
   - プロファイリング統合
   - トレンド分析

### テスト計画

1. **ユニットテスト**
   - ベンチマークデコレータのテスト
   - レコーダーのテスト
   - レポーターのテスト

2. **統合テスト**
   - 実際のドキュメント生成処理での測定
   - CLIコマンドのテスト

3. **パフォーマンステスト**
   - ベンチマークツール自体のオーバーヘッド測定
   - 大量データでの動作確認

## 次のステップ

この計画に同意いただけましたら、以下の順序で実装を開始します：

1. **フェーズ1**: コアベンチマーク機能の実装
2. **フェーズ2**: 主要処理への統合
3. **フェーズ3**: CLI統合とレポート生成

各フェーズの完了後に動作確認とフィードバックをいただき、必要に応じて調整を行います。

