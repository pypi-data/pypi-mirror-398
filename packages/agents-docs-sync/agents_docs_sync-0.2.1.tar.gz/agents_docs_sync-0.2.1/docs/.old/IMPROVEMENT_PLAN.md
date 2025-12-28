# Python以外の言語サポート改善計画

## 問題の概要

他のプロジェクトで使用した際に、Python以外の言語（JavaScript、TypeScript、Go、Rustなど）での動作がうまくいかない問題が報告されています。

## 現状分析

### 1. パーサー選択の問題

**問題点:**
- `APIGenerator._get_parsers()`で言語に応じてパーサーを選択しているが、以下の問題がある：
  - JavaScript/TypeScriptは`JSParser`を使用（同一パーサー）
  - その他の言語は`GenericParser`を使用
  - `GenericParser`は言語名を受け取るが、実際のパターンマッチングが不十分

**該当コード:**
```python
# docgen/generators/api_generator.py:211-228
def _get_parsers(self) -> list["BaseParser"]:
    parsers = []
    for lang in self.languages:
        if lang == "python":
            parsers.append(PythonParser(self.project_root))
        elif lang in ["javascript", "typescript"]:
            parsers.append(JSParser(self.project_root))
        else:
            parsers.append(GenericParser(self.project_root, language=lang))
    return parsers
```

### 2. 拡張子マッピングの不整合

**問題点:**
- `GenericParser.get_supported_extensions()`は言語に応じた拡張子を返すが、`DetectorPatterns.SOURCE_EXTENSIONS`と完全に一致していない
- TypeScriptの拡張子（`.ts`, `.tsx`, `.d.ts`）が`JSParser`で正しく処理されていない可能性

**該当コード:**
```python
# docgen/generators/parsers/generic_parser.py:143-168
def get_supported_extensions(self) -> list[str]:
    extension_map = {
        "rust": [".rs"],
        "java": [".java"],
        # ... 他の言語
        "go": [".go"],
    }
    return extension_map.get(self.language, [".txt"])
```

### 3. エラーハンドリングの不足

**問題点:**
- パーサーが失敗した場合、`logger.warning()`でログ出力されるが、具体的な問題点が分かりにくい
- 言語ごとのエラー情報が不足している
- パーサーが空の結果を返した場合とエラーが発生した場合の区別が不十分

**該当コード:**
```python
# docgen/generators/parsers/base_parser.py:256, 269
logger.warning(f"{file_path} の解析に失敗しました: {e}")
```

### 4. 言語検出とパーサーの連携不足

**問題点:**
- 言語検出は`UnifiedDetector`で行われ、設定ファイル（`.toml`）から情報を読み込む
- しかし、実際のパーサーとの連携が不十分で、検出された言語がパーサーで正しく処理されない可能性

### 5. TypeScriptの扱い

**問題点:**
- TypeScriptとJavaScriptが同じ`JSParser`を使用するが、拡張子が異なる（`.ts`, `.tsx` vs `.js`, `.jsx`）
- `JSParser.get_supported_extensions()`は両方の拡張子を返すが、実際の解析ロジックがTypeScript固有の構文に対応していない可能性

## 改善計画

### Phase 1: パーサー選択ロジックの改善

#### 1.1 パーサーファクトリーの導入

**目的:** 言語とパーサーの対応を一元管理し、拡張性を向上させる

**実装内容:**
- `ParserFactory`クラスを作成
- 言語名から適切なパーサーを選択するロジックを集約
- 新しい言語の追加が容易になる

**ファイル:**
- `docgen/generators/parsers/parser_factory.py` (新規作成)

#### 1.2 言語別パーサーの明確化

**目的:** 各言語に最適なパーサーを選択

**実装内容:**
- Go専用パーサー（`GoParser`）の作成を検討
- Rust専用パーサー（`RustParser`）の作成を検討
- TypeScript専用パーサー（`TypeScriptParser`）の作成を検討

**優先度:** 中（まずは`GenericParser`の改善を優先）

### Phase 2: GenericParserの改善

#### 2.1 拡張子マッピングの統一

**目的:** `DetectorPatterns.SOURCE_EXTENSIONS`と`GenericParser`の拡張子マッピングを統一

**実装内容:**
- `GenericParser.get_supported_extensions()`を`DetectorPatterns`から取得するように変更
- 言語ごとの拡張子定義を一元化

**ファイル:**
- `docgen/generators/parsers/generic_parser.py`

#### 2.2 パターンマッチングの改善

**目的:** 各言語のコメント形式と関数定義パターンをより正確に検出

**実装内容:**
- Go言語の`//`コメントと`func`定義のパターンを改善
- Rust言語の`//!`ドキュメントコメントのサポート
- Java言語のJavadocコメントの改善

**ファイル:**
- `docgen/generators/parsers/generic_parser.py`

#### 2.3 エラーハンドリングの強化

**目的:** パーサーエラーの詳細情報を提供

**実装内容:**
- 言語名、ファイルパス、エラー内容を含む詳細なエラーメッセージ
- パーサーが空の結果を返した場合の警告メッセージ
- 言語ごとのエラー統計情報

**ファイル:**
- `docgen/generators/parsers/base_parser.py`
- `docgen/generators/parsers/generic_parser.py`

### Phase 3: TypeScriptサポートの改善

#### 3.1 TypeScript専用パーサーの検討

**目的:** TypeScript固有の構文（型定義、インターフェースなど）を正しく解析

**実装内容:**
- `TypeScriptParser`クラスの作成
- TypeScript固有の構文パターンの追加
- `.d.ts`ファイルの処理

**優先度:** 低（まずは`JSParser`の改善を優先）

#### 3.2 JSParserの改善

**目的:** TypeScriptの拡張子を正しく処理

**実装内容:**
- `.ts`, `.tsx`, `.d.ts`ファイルの処理を改善
- TypeScript固有の構文（`interface`, `type`, `enum`など）の抽出

**ファイル:**
- `docgen/generators/parsers/js_parser.py`

### Phase 4: テストと検証

#### 4.1 非Python言語のテストケース追加

**目的:** 各言語での動作を検証

**実装内容:**
- JavaScript/TypeScriptプロジェクトのテストケース
- Goプロジェクトのテストケース
- Rustプロジェクトのテストケース
- その他の言語のテストケース

**ファイル:**
- `tests/integration/test_non_python_languages.py` (新規作成)

#### 4.2 エラーケースのテスト

**目的:** パーサーエラー時の動作を検証

**実装内容:**
- 構文エラーのあるファイルの処理
- サポートされていない言語の処理
- 空のプロジェクトの処理

**ファイル:**
- `tests/integration/test_parser_errors.py` (新規作成)

### Phase 5: ドキュメントとログの改善

#### 5.1 ログメッセージの改善

**目的:** 問題の特定を容易にする

**実装内容:**
- 言語ごとの解析結果の統計情報
- パーサーエラーの詳細ログ
- サポートされていない言語の警告

**ファイル:**
- `docgen/generators/api_generator.py`
- `docgen/generators/parsers/base_parser.py`

#### 5.2 ドキュメントの更新

**目的:** サポートされている言語と制限事項を明確化

**実装内容:**
- READMEにサポート言語の一覧を追加
- 各言語のサポート状況を記載
- 既知の問題点を記載

**ファイル:**
- `README.md`
- `docs/LANGUAGE_SUPPORT.md` (新規作成)

## 実装優先順位

### 高優先度（即座に対応）

1. **GenericParserの拡張子マッピング統一** (Phase 2.1)
   - 影響: 高
   - 工数: 低
   - リスク: 低

2. **エラーハンドリングの強化** (Phase 2.3)
   - 影響: 高
   - 工数: 中
   - リスク: 低

3. **パーサーファクトリーの導入** (Phase 1.1)
   - 影響: 中
   - 工数: 中
   - リスク: 低

### 中優先度（短期対応）

4. **GenericParserのパターンマッチング改善** (Phase 2.2)
   - 影響: 中
   - 工数: 高
   - リスク: 中

5. **非Python言語のテストケース追加** (Phase 4.1)
   - 影響: 中
   - 工数: 高
   - リスク: 低

### 低優先度（長期対応）

6. **TypeScript専用パーサーの作成** (Phase 3.1)
   - 影響: 低
   - 工数: 高
   - リスク: 中

7. **言語別専用パーサーの作成** (Phase 1.2)
   - 影響: 低
   - 工数: 非常に高
   - リスク: 中

## 期待される効果

1. **互換性の向上**: Python以外の言語でも正しく動作する
2. **エラー情報の明確化**: 問題が発生した場合、原因を特定しやすくなる
3. **保守性の向上**: パーサー選択ロジックが一元化され、保守が容易になる
4. **拡張性の向上**: 新しい言語の追加が容易になる

## リスクと対策

### リスク1: 既存のPythonプロジェクトへの影響

**対策:**
- 既存のテストケースをすべて実行して回帰テストを実施
- Pythonパーサーは変更しない

### リスク2: パフォーマンスの低下

**対策:**
- パーサーの選択ロジックを最適化
- キャッシュ機能を活用

### リスク3: 新しいバグの導入

**対策:**
- 段階的な実装とテスト
- コードレビューの実施

## 次のステップ

1. Phase 2.1の実装（拡張子マッピングの統一）
2. Phase 2.3の実装（エラーハンドリングの強化）
3. Phase 1.1の実装（パーサーファクトリーの導入）
4. テストケースの追加と検証
5. ドキュメントの更新

