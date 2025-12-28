# アーキテクチャ検出器修正 - JavaScript/TypeScript詳細解析追加

## 修正日: 2025-12-23

## 問題

アーキテクチャ検出器がJavaScript/TypeScriptプロジェクトを検出できていましたが、詳細な情報（依存関係、モジュール構造）を抽出できていませんでした。

## 原因

`GenericDetector`はJavaScript/TypeScriptプロジェクトを検出していましたが、`package.json`を解析して依存関係やモジュール構造を抽出する機能がありませんでした。`PythonDetector`のように、設定ファイルを解析して詳細情報を抽出する必要がありました。

## 修正内容

### ファイル: `docgen/archgen/detectors/generic_detector.py`

1. **JavaScript/TypeScript専用の検出メソッドを追加**
   - `_detect_javascript_typescript()`メソッドを新規作成
   - `package.json`を解析してプロジェクト情報を抽出

2. **`package.json`解析機能**
   - プロジェクト名、バージョン、説明を抽出
   - `dependencies`と`devDependencies`から依存関係を抽出
   - TypeScriptかどうかを判定（`typescript`パッケージの存在、`tsconfig.json`の存在）

3. **モジュール構造のスキャン機能**
   - `_scan_js_modules()`メソッドを追加
   - `src`, `lib`, `app`, `components`, `pages`などのディレクトリを探索
   - `_scan_js_directory()`メソッドで再帰的にディレクトリ構造をスキャン

4. **`detect()`メソッドの改善**
   - JavaScript/TypeScriptプロジェクトを優先的に詳細解析
   - 他の言語は従来通り検出

## 実装詳細

### `package.json`解析

```python
def _detect_javascript_typescript(self, project_root: Path) -> Service | None:
    package_json = project_root / "package.json"
    if not package_json.exists():
        return None

    package_data = safe_read_json(package_json)
    # dependenciesとdevDependenciesを抽出
    # TypeScriptかどうかを判定
    # モジュール構造をスキャン
```

### モジュール構造のスキャン

- `src`ディレクトリを優先的に探索（最大深度3）
- `lib`, `app`, `components`, `pages`ディレクトリも探索（最大深度2）
- 各ディレクトリ内のJavaScript/TypeScriptファイルを検出
- 再帰的にサブモジュールを抽出

## 期待される効果

1. ✅ JavaScript/TypeScriptプロジェクトの依存関係が正しく抽出される
2. ✅ モジュール構造がアーキテクチャ図に反映される
3. ✅ プロジェクト名、バージョンなどのメタデータが正しく表示される
4. ✅ TypeScriptとJavaScriptが正しく区別される

## 制限事項

- モジュール構造のスキャンは、一般的なディレクトリ構造（`src`, `lib`, `app`など）を想定しています
- カスタムディレクトリ構造の場合は、モジュールが検出されない可能性があります
- 依存関係の解析は`package.json`のみを対象としています（`yarn.lock`や`package-lock.json`は解析していません）

## テスト推奨事項

以下のテストを実施することを推奨します:

1. **JavaScript/TypeScriptプロジェクトでのアーキテクチャ検出**
   - `package.json`が正しく解析されるか
   - 依存関係が正しく抽出されるか
   - モジュール構造が正しく検出されるか

2. **TypeScriptプロジェクトの識別**
   - TypeScriptプロジェクトが正しく識別されるか
   - JavaScriptプロジェクトとTypeScriptプロジェクトが区別されるか

3. **エッジケースの確認**
   - `package.json`がないプロジェクト
   - カスタムディレクトリ構造のプロジェクト
   - 空のプロジェクト

