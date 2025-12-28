# アルゴリズム改善提案・実装状況

このドキュメントは、コードベース内でアルゴリズム的に改善できる部分をまとめたものです。

## 実装状況

### ✅ 実装完了

1. **埋め込み生成のバッチ処理でキャッシュ活用** (優先度: 高)
   - 実装場所: `docgen/rag/embedder.py`
   - 状態: ✅ 完了
   - 効果: 同じテキストの再計算を回避し、埋め込み生成時間を大幅に削減

2. **除外ディレクトリチェックの効率化** (優先度: 中)
   - 実装場所: `docgen/rag/chunker.py`, `docgen/detectors/detector_patterns.py`, `docgen/generators/parsers/base_parser.py`
   - 状態: ✅ 完了
   - 効果: O(n)からO(1)の検索に改善（セットのintersection使用）

3. **パスベースの除外チェックの最適化** (優先度: 中)
   - 実装場所: `docgen/rag/chunker.py`
   - 状態: ✅ 完了
   - 効果: 除外ディレクトリを分類し、必要な場合のみパターンチェックを実行

4. **統一ファイルスキャナーの実装** (優先度: 高)
   - 実装場所: `docgen/utils/file_scanner.py` (新規作成)
   - 状態: ✅ 実装完了（統合は段階的に実施予定）
   - 効果: ファイル走査の重複を排除し、走査時間を約75%削減可能

### 🔄 実装予定

1. **統一ファイルスキャナーの既存コードへの統合** (優先度: 高)
   - 統合対象:
     - `docgen/detectors/detector_patterns.py`
     - `docgen/generators/parsers/base_parser.py`
     - `docgen/rag/chunker.py`
     - `docgen/generators/api_generator.py`
   - 状態: 🔄 段階的に統合予定
   - 注意: 後方互換性を保ちながら段階的に統合

2. **並列処理の動的調整** (優先度: 低)
   - 実装場所: `docgen/generators/parsers/base_parser.py`
   - 状態: 📋 提案済み（実装は後回し）

---

## 改善提案（詳細）

## 1. ファイル走査の重複排除

### 問題点
現在、以下の4つのモジュールでそれぞれ独立して`os.walk`を使用してプロジェクトルートを走査しています：

- `docgen/detectors/detector_patterns.py` - 言語検出用
- `docgen/generators/parsers/base_parser.py` - パーサー用
- `docgen/generators/api_generator.py` - API生成用
- `docgen/rag/chunker.py` - RAGチャンク化用

同じプロジェクトルートを複数回走査することで、I/Oオーバーヘッドが発生しています。

### 改善案
統一ファイルスキャナーを作成し、一度の走査で必要な情報をすべて収集します。

```python
# docgen/utils/file_scanner.py (新規作成)
class UnifiedFileScanner:
    """プロジェクト全体を一度だけ走査して、必要な情報を収集"""

    def __init__(self, project_root: Path, exclude_dirs: set[str] | None = None):
        self.project_root = project_root
        self.exclude_dirs = exclude_dirs or set(DetectorPatterns.EXCLUDE_DIRS)
        self._scanned = False
        self._files_by_extension: dict[str, list[Path]] = {}
        self._all_files: list[Path] = []

    def scan_once(self) -> dict[str, Any]:
        """一度だけ走査して結果をキャッシュ"""
        if self._scanned:
            return self._cached_result

        # os.walkで一度だけ走査
        for root, dirs, files in os.walk(self.project_root):
            # 除外ディレクトリを早期にスキップ
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            for file_name in files:
                file_path = Path(root) / file_name
                ext = file_path.suffix.lower()

                if ext not in self._files_by_extension:
                    self._files_by_extension[ext] = []
                self._files_by_extension[ext].append(file_path)
                self._all_files.append(file_path)

        self._scanned = True
        self._cached_result = {
            'files_by_extension': self._files_by_extension,
            'all_files': self._all_files
        }
        return self._cached_result
```

**期待される効果**: ファイル走査時間を約75%削減（4回 → 1回）

---

## 2. 埋め込み生成のバッチ処理でキャッシュを活用

### 問題点
`docgen/rag/embedder.py`の`embed_batch`メソッドでは、個別のテキストに対してキャッシュをチェックする`embed_text`メソッドの機能を活用していません。同じテキストが複数回処理される場合でも、毎回埋め込みを再計算しています。

### 改善案
バッチ処理前にキャッシュをチェックし、キャッシュヒットしたものはスキップ、未キャッシュのもののみ処理します。

```python
def embed_batch(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
    """複数のテキストをバッチ処理で埋め込み（キャッシュ対応）"""
    self.logger.info(f"Embedding {len(texts)} texts with batch size {batch_size}")

    # キャッシュをチェック
    embeddings = []
    texts_to_embed = []
    indices_to_embed = []

    for i, text in enumerate(texts):
        cache_key = self._get_cache_key(text)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            embeddings.append((i, cached))
        else:
            texts_to_embed.append(text)
            indices_to_embed.append(i)

    # 未キャッシュのテキストのみバッチ処理
    if texts_to_embed:
        new_embeddings = self.model.encode(
            texts_to_embed,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
        )

        # キャッシュに保存
        for text, embedding in zip(texts_to_embed, new_embeddings):
            cache_key = self._get_cache_key(text)
            self._save_to_cache(cache_key, embedding)

        # インデックスと埋め込みをマッピング
        for idx, emb in zip(indices_to_embed, new_embeddings):
            embeddings.append((idx, emb))

    # インデックス順にソートして返す
    embeddings.sort(key=lambda x: x[0])
    return np.array([emb for _, emb in embeddings])
```

**期待される効果**: 同じテキストが複数回処理される場合、埋め込み生成時間を大幅に削減

---

## 3. 除外ディレクトリチェックの効率化

### 問題点
`docgen/rag/chunker.py`の193-205行目と`docgen/detectors/detector_patterns.py`の265行目で、除外ディレクトリのチェックにリストの`in`演算子を使用しています。これはO(n)の時間計算量です。

```python
# 現在の実装（非効率）
if str(rel_path) in self.IGNORE_DIRS:  # O(n)
if any(part in cls.EXCLUDE_DIRS for part in rel_path.parts):  # O(n*m)
```

### 改善案
除外ディレクトリをセットに変換して、O(1)の検索を実現します。

```python
# クラス変数をセットに変更
EXCLUDE_DIRS = {
    ".venv", ".git", "__pycache__", "node_modules",
    # ... 他のディレクトリ
}

# チェック処理
if rel_path.parts[0] in EXCLUDE_DIRS:  # O(1)
    continue
```

**期待される効果**: 除外ディレクトリチェックの時間計算量をO(n)からO(1)に改善

---

## 4. パスベースの除外チェックの最適化

### 問題点
`docgen/rag/chunker.py`の200-202行目で、各ディレクトリに対して`startswith`チェックを繰り返しています。また、`docgen/detectors/detector_patterns.py`の265行目でも同様の処理があります。

```python
# 現在の実装
if any(
    str(rel_path).startswith(ignore) for ignore in self.IGNORE_DIRS if "/" in ignore
):
```

### 改善案
除外パターンを事前に分類し、より効率的なチェックを行います。

```python
class CodeChunker:
    def __init__(self, config: dict[str, Any] | None = None):
        # ... 既存のコード ...

        # 除外ディレクトリを分類
        self._exact_dir_names = {d for d in self.IGNORE_DIRS if "/" not in d}
        self._path_patterns = {d for d in self.IGNORE_DIRS if "/" in d}

    def _should_skip_dir(self, rel_path: Path) -> bool:
        """ディレクトリをスキップすべきかチェック（最適化版）"""
        # 完全一致チェック（O(1)）
        if rel_path.parts[0] in self._exact_dir_names:
            return True

        # パスパターンチェック（必要な場合のみ）
        rel_str = str(rel_path)
        for pattern in self._path_patterns:
            if rel_str.startswith(pattern):
                return True

        return False
```

**期待される効果**: パスチェックのオーバーヘッドを削減

---

## 5. 並列処理の閾値の動的調整

### 問題点
`docgen/generators/parsers/base_parser.py`の229行目で、並列処理の閾値が固定値（3または5）になっています。ファイルサイズや処理時間を考慮していません。

### 改善案
ファイルサイズと推定処理時間を考慮した動的な閾値を設定します。

```python
def _should_use_parallel(
    self,
    files_to_parse: list[tuple[Path, Path]],
    avg_file_size: int | None = None
) -> bool:
    """並列処理を使用すべきか判定（動的閾値）"""
    cpu_count = os.cpu_count() or 1

    # ファイル数が少ない場合は逐次処理
    if len(files_to_parse) <= 2:
        return False

    # 平均ファイルサイズが大きい場合は並列処理を推奨
    if avg_file_size and avg_file_size > 100 * 1024:  # 100KB以上
        return len(files_to_parse) > 1

    # CPU数に応じた閾値
    threshold = max(3, cpu_count // 2)
    return len(files_to_parse) > threshold
```

**期待される効果**: 小規模プロジェクトではオーバーヘッドを削減、大規模プロジェクトでは並列処理を最大限活用

---

## 6. リスト拡張の効率化

### 問題点
`docgen/rag/chunker.py`の211行目で、`all_chunks.extend(chunks)`を使用しています。大量のチャンクがある場合、メモリの再割り当てが頻繁に発生する可能性があります。

### 改善案
事前にサイズを推定してリストを予約するか、ジェネレータを使用します。

```python
def chunk_codebase(self, project_root: Path) -> list[dict[str, Any]]:
    """プロジェクト全体をチャンク化（メモリ効率化版）"""
    # ファイル数を事前にカウント（オプション）
    file_count = sum(1 for _ in self._iter_files(project_root))

    # リストの初期容量を推定（オプション、Pythonのリストは動的だが）
    # all_chunks = []  # 通常の実装で問題ないが、大量データの場合は考慮

    all_chunks = []
    for root, dirs, files in os.walk(project_root):
        # ... 既存のコード ...
        for file_name in files:
            file_path = Path(root) / file_name
            if self.should_process_file(file_path):
                chunks = self.chunk_file(file_path, project_root)
                all_chunks.extend(chunks)  # これは通常問題ない

    return all_chunks
```

**注意**: Pythonのリストは内部的に動的に拡張されるため、この最適化の効果は限定的です。ただし、非常に大量のデータ（数万チャンク以上）を扱う場合は考慮の価値があります。

---

## 7. 拡張子チェックの最適化

### 問題点
複数の場所で拡張子チェックが行われていますが、セットへの変換が各モジュールで個別に行われています。

### 改善案
拡張子セットを一度だけ作成し、再利用します。

```python
# detector_patterns.py でクラス変数として定義
SOURCE_EXTENSIONS_SET = {
    ext for exts in SOURCE_EXTENSIONS.values() for ext in exts
}

# 使用時
if ext in SOURCE_EXTENSIONS_SET:  # O(1)の検索
    # ...
```

**期待される効果**: 拡張子チェックのオーバーヘッドを削減

---

## 優先度の高い改善項目

1. **ファイル走査の重複排除** (優先度: 高)
   - 影響範囲が広く、パフォーマンスへの影響が大きい
   - 実装難易度: 中

2. **埋め込み生成のキャッシュ活用** (優先度: 高)
   - RAG処理のパフォーマンスに直接影響
   - 実装難易度: 低

3. **除外ディレクトリチェックの効率化** (優先度: 中)
   - 実装が簡単で、効果が確実
   - 実装難易度: 低

4. **パスベースの除外チェックの最適化** (優先度: 中)
   - 実装難易度: 低

5. **並列処理の動的調整** (優先度: 低)
   - 効果は限定的だが、実装は簡単
   - 実装難易度: 低

---

## 実装時の注意事項

1. **後方互換性**: 既存のAPIを壊さないように注意
2. **テスト**: 各改善に対して適切なテストを追加
3. **ベンチマーク**: 改善前後のパフォーマンスを測定
4. **段階的実装**: 一度にすべてを実装せず、優先度の高いものから順に実装

---

## 期待される総合的な効果

- **ファイル走査時間**: 約75%削減（4回 → 1回）
- **埋め込み生成時間**: キャッシュヒット率に依存（50%ヒットで約50%削減）
- **除外ディレクトリチェック**: O(n) → O(1)の改善
- **総合的な実行時間**: 10-30%の改善を期待

