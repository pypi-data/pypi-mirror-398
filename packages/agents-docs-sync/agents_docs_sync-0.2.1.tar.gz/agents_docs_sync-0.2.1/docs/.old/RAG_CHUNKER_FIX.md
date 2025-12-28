# RAGチャンカー修正 - JavaScript/TypeScriptサポート追加

## 修正日: 2025-12-23

## 問題

RAGチャンカーがJavaScript/TypeScriptファイルを認識せず、チャンクが0件になっていました。

**エラーログ:**
```
Created 0 chunks from codebase
チャンクが見つかりませんでした
```

## 原因

`CodeChunkStrategy`クラスが以下のファイル形式しか処理していませんでした：
- `.py` (Python)
- `.yaml`, `.yml` (YAML)
- `.toml` (TOML)

JavaScript/TypeScriptファイル（`.js`, `.jsx`, `.ts`, `.tsx`, `.d.ts`など）は`CodeChunkStrategy`に渡されていましたが、空のリストを返していました。

## 修正内容

### ファイル: `docgen/rag/strategies/code_strategy.py`

1. **JavaScript/TypeScriptファイルのサポート追加**
   - `chunk()`メソッドに`.js`, `.jsx`, `.mjs`, `.cjs`, `.ts`, `.tsx`, `.d.ts`の処理を追加
   - `_chunk_javascript()`メソッドを新規作成

2. **`_chunk_javascript()`メソッドの実装**
   - 正規表現ベースで関数、クラス、インターフェース/型定義を抽出
   - 関数定義パターン:
     - `function name()`
     - `const name = () =>`
     - `name: () =>`
     - メソッド定義
   - クラス定義パターン: `class Name`
   - インターフェース/型定義パターン（TypeScript）: `interface Name`, `type Name`
   - 各要素を個別のチャンクとして抽出
   - 要素が見つからない場合はファイル全体を1つのチャンクとして返す

3. **フォールバック処理の改善**
   - サポートされていないコードファイルも、空のリストではなくファイル全体を1つのチャンクとして返すように変更

## 実装詳細

### 関数抽出パターン

```python
function_patterns = [
    r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(",
    r"(?:export\s+)?(?:async\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>",
    r"(?:export\s+)?(?:async\s+)?(\w+)\s*:\s*(?:async\s+)?\([^)]*\)\s*=>",
    r"(?:export\s+)?(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{",
]
```

### クラス/インターフェース抽出パターン

```python
class_pattern = r"(?:export\s+)?class\s+(\w+)"
interface_pattern = r"(?:export\s+)?(?:interface|type)\s+(\w+)"
```

## 期待される効果

1. ✅ JavaScript/TypeScriptファイルからチャンクが生成される
2. ✅ RAGインデックスが正常に構築される
3. ✅ README生成時にRAGコンテキストが利用可能になる

## 制限事項

- 正規表現ベースのパターンマッチングのため、複雑な構文（ネストされた関数など）では正確に動作しない可能性があります
- より正確な解析には、JavaScript/TypeScript用のASTパーサー（esprima、@babel/parserなど）の使用を検討できます

## テスト推奨事項

以下のテストを実施することを推奨します:

1. **JavaScript/TypeScriptプロジェクトでのRAGインデックス構築**
   - チャンクが正しく生成されるか
   - 関数、クラス、インターフェースが個別のチャンクとして抽出されるか

2. **RAG検索の動作確認**
   - 生成されたチャンクがRAG検索で利用可能か
   - README生成時にRAGコンテキストが正しく取得されるか

3. **エッジケースの確認**
   - 複雑な構文のファイル
   - 空のファイル
   - 構文エラーのあるファイル

