# リファクタリング計画

作成日: 2025-12-24
最終更新: 2025-12-24

## 概要

このドキュメントは、`agents-docs-sync` プロジェクトの包括的なリファクタリング計画をまとめたものです。コード品質の向上、保守性の改善、技術的負債の削減を目的としています。

## 現状分析

### 発見された主要な問題

1. **インポートパスの問題** (高優先度)
   - `sys.path.insert()` が14箇所で使用されている
   - パッケージ構造に適さない実装
   - 相対インポートへの移行が必要

2. **例外処理の不整合** (高優先度)
   - 広すぎる例外処理（`except Exception`）が11箇所
   - 例外タイプの不統一（`ValueError` vs `ConfigError`）
   - エラーハンドリングの標準化が必要

3. **コード重複** (中優先度)
   - ジェネレーター間の共通コード
   - LLMクライアントの重複メソッド（レビューで指摘）
   - 共通ロジックの抽出が必要

4. **型ヒントの不足** (中優先度)
   - 一部のメソッドで型ヒントが不完全
   - 一貫性のない型アノテーション
   - 型安全性の向上が必要

5. **統一ファイルスキャナーの未統合** (中優先度)
   - `UnifiedFileScanner` が実装済みだが未使用
   - 4つのモジュールで独立したファイル走査を実行
   - パフォーマンス改善の機会を逃している

6. **メソッドの複雑度** (低優先度)
   - 一部のメソッドが複雑すぎる
   - 単一責任の原則に違反している可能性

## リファクタリングフェーズ

### フェーズ1: インポートパスの改善（高優先度）

#### 目標
- `sys.path.insert()` の使用を削除
- 適切な相対インポートへの移行
- パッケージ構造の明確化

#### タスク1.1: メインモジュールのインポート修正
**対象ファイル**:
- `docgen/docgen.py` (1箇所)
- `docgen/collectors/command_help_extractor.py` (3箇所)

**作業内容**:
- `sys.path.insert()` を削除
- 相対インポートまたは絶対インポートに変更
- パッケージとしてインストールされた場合の動作を確認

**影響範囲**:
- エントリーポイントの動作確認が必要
- テストファイルのインポートパスも修正が必要

#### タスク1.2: テストファイルのインポート修正
**対象ファイル**:
- `tests/integration/test_integration.py`
- `tests/integration/test_document_generator.py`
- `tests/unit/test_docgen.py`
- `tests/integration/test_edge_cases.py`
- `tests/integration/test_language_info_collector.py`
- `tests/unit/test_generator_factory.py`
- `tests/integration/test_project_info_collector.py`
- `tests/test_config/test_config_accessor.py`

**作業内容**:
- `sys.path.insert()` を削除
- `pytest` のパス解決機能を活用
- `conftest.py` で共通のパス設定を管理

#### タスク1.3: スクリプトファイルのインポート修正
**対象ファイル**:
- `scripts/verify_language_detector.py`
- `scripts/run_tests.sh` (シェルスクリプト)

**作業内容**:
- Pythonスクリプト: 相対インポートまたは `PYTHONPATH` 環境変数の使用
- シェルスクリプト: `PYTHONPATH` の設定を確認

**検証方法**:
```bash
# パッケージとしてインストールしてテスト
uv pip install -e .
python -m docgen.docgen --help

# テスト実行
uv run pytest tests/ -v
```

**完了基準**:
- [ ] すべての `sys.path.insert()` が削除された
- [ ] すべてのテストが正常に実行できる
- [ ] パッケージとしてインストールして動作確認済み

---

### フェーズ2: 例外処理の標準化（高優先度）

#### 目標
- 適切な例外タイプの使用
- 例外処理の一貫性確保
- エラーメッセージの明確化

#### タスク2.1: カスタム例外クラスの確認と拡張
**対象ファイル**:
- `docgen/utils/exceptions.py`

**作業内容**:
- 既存の例外クラスを確認
- 不足している例外クラスを追加
- 例外階層の整理

**確認事項**:
- `ConfigError` が適切に定義されているか
- 各モジュール固有の例外が必要か

#### タスク2.2: 広すぎる例外処理の修正
**対象ファイル**:
- `docgen/generators/agents_generator.py` (3箇所)
- `docgen/generators/base_generator.py` (4箇所)
- `docgen/generators/api_generator.py` (1箇所)
- `docgen/generators/readme_generator.py` (2箇所)
- `docgen/validators/implementation_validator.py` (1箇所)

**作業内容**:
- `except Exception` を具体的な例外タイプに変更
- 適切な例外ハンドリングの実装
- ログ出力の改善

**修正例**:
```python
# 修正前
try:
    # 処理
except Exception as e:
    logger.error(f"エラー: {e}")

# 修正後
try:
    # 処理
except (ValueError, FileNotFoundError) as e:
    logger.error(f"設定エラー: {e}")
    raise ConfigError(f"設定の読み込みに失敗しました: {e}") from e
except Exception as e:
    logger.error(f"予期しないエラー: {e}", exc_info=True)
    raise
```

#### タスク2.3: LLMクライアントの例外処理統一
**対象ファイル**:
- `docgen/utils/llm/anthropic_client.py`
- `docgen/utils/llm/openai_client.py`
- `docgen/utils/llm/local_client.py`

**作業内容**:
- `ValueError` を `ConfigError` に統一
- 例外メッセージの標準化
- エラーコードの追加（必要に応じて）

**完了基準**:
- [ ] すべての `except Exception` が具体的な例外タイプに変更された
- [ ] 例外処理が一貫している
- [ ] エラーメッセージが明確で有用である
- [ ] テストで例外処理が適切に検証されている

---

### フェーズ3: コード重複の削減（中優先度）

#### 目標
- 共通ロジックの抽出
- DRY原則の遵守
- 保守性の向上

#### タスク3.1: ジェネレーター間の共通コード抽出
**対象ファイル**:
- `docgen/generators/base_generator.py`
- `docgen/generators/agents_generator.py`
- `docgen/generators/readme_generator.py`

**共通化対象メソッド** (レビュー結果より):
1. `_generate_llm_setup_section` - LLMセットアップセクション
2. `_generate_pr_section` - プルリクエスト手順
3. `_generate_custom_instructions_section` - カスタム指示セクション
4. `_generate_coding_standards_section` - コーディング規約セクション
5. `_generate_setup_section` - セットアップセクション（依存関係部分）
6. `_generate_build_test_section` - ビルド・テストセクション

**作業内容**:
- 共通ロジックを `BaseGenerator` に移動
- サブクラスでカスタマイズ可能な部分は抽象メソッドまたはフックとして実装
- テンプレート変数を使用して柔軟性を確保

**実装方針**:
```python
# BaseGenerator に追加
def _generate_common_section(self, section_name: str, **kwargs) -> str:
    """共通セクション生成のベースメソッド"""
    template = self.template_service.get_template(section_name)
    return template.render(**kwargs)

# サブクラスでオーバーライド可能
def _generate_custom_instructions_section(self) -> str:
    """カスタム指示セクション（デフォルト実装）"""
    return self._generate_common_section("custom_instructions", ...)
```

#### タスク3.2: LLMクライアントの重複メソッド削除
**対象ファイル**:
- `docgen/utils/llm/base.py`
- `docgen/utils/llm/openai_client.py`
- `docgen/utils/llm/anthropic_client.py`

**作業内容**:
- `_create_outlines_model_internal` の重複を確認
- 基底クラスに共通実装を移動（可能な場合）
- プロバイダー固有の実装のみをサブクラスに残す

**完了基準**:
- [ ] ジェネレーター間のコード重複が削減された
- [ ] LLMクライアントの重複メソッドが削除された
- [ ] すべてのテストが正常に実行できる
- [ ] 機能に影響がないことを確認

---

### フェーズ4: 統一ファイルスキャナーの統合（中優先度）

#### 目標
- ファイル走査の重複排除
- パフォーマンスの向上（約75%の削減見込み）
- コードの一貫性向上

#### タスク4.1: 統合対象モジュールの特定
**対象モジュール**:
- `docgen/detectors/detector_patterns.py`
- `docgen/generators/parsers/base_parser.py`
- `docgen/rag/chunker.py`
- `docgen/generators/api_generator.py`

**作業内容**:
- 各モジュールのファイル走査ロジックを確認
- `UnifiedFileScanner` への移行計画を策定
- 段階的な統合計画を作成

#### タスク4.2: 段階的統合の実施
**フェーズ4.2.1: APIジェネレーターの統合**
- `docgen/generators/api_generator.py` を `UnifiedFileScanner` に移行
- テストで動作確認

**フェーズ4.2.2: パーサーの統合**
- `docgen/generators/parsers/base_parser.py` を統合
- 言語固有のパーサーへの影響を確認

**フェーズ4.2.3: 検出器の統合**
- `docgen/detectors/detector_patterns.py` を統合
- パフォーマンステストを実施

**フェーズ4.2.4: RAGチャンカーの統合**
- `docgen/rag/chunker.py` を統合
- 最終的なパフォーマンス改善を測定

**実装例**:
```python
# 統合前
def scan_files(self, project_root: Path):
    for root, dirs, files in os.walk(project_root):
        # 処理

# 統合後
def __init__(self, project_root: Path, file_scanner: UnifiedFileScanner):
    self.file_scanner = file_scanner
    self.scan_result = file_scanner.scan_once()

def scan_files(self, project_root: Path):
    # scan_result を使用
    files = self.scan_result.get("files_by_extension", {}).get(".py", [])
```

**完了基準**:
- [ ] すべての対象モジュールが `UnifiedFileScanner` を使用している
- [ ] パフォーマンステストで改善を確認
- [ ] すべてのテストが正常に実行できる
- [ ] 機能に影響がないことを確認

---

### フェーズ5: 型ヒントの追加と改善（中優先度）

#### 目標
- 型安全性の向上
- IDE支援の改善
- コードの可読性向上

#### タスク5.1: 型ヒントの不足箇所の特定
**作業内容**:
- `mypy` または `pyright` で型チェックを実行
- 型ヒントが不足している箇所をリストアップ
- 優先順位を決定

**実行コマンド**:
```bash
# mypy を使用する場合
uv run mypy docgen/ --ignore-missing-imports

# pyright を使用する場合
uv run pyright docgen/
```

#### タスク5.2: 型ヒントの追加
**対象**:
- パブリックメソッドの戻り値型
- 関数パラメータの型
- クラス属性の型

**作業内容**:
- `typing` モジュールの適切な使用
- `TYPE_CHECKING` を使用した循環インポートの回避
- ジェネリック型の適切な使用

**完了基準**:
- [ ] すべてのパブリックAPIに型ヒントが追加された
- [ ] 型チェッカーでエラーが発生しない
- [ ] 既存の機能に影響がない

---

### フェーズ6: メソッドの複雑度削減（低優先度）

#### 目標
- 単一責任の原則の遵守
- コードの可読性向上
- テストの容易性向上

#### タスク6.1: 複雑なメソッドの特定
**作業内容**:
- 循環的複雑度（Cyclomatic Complexity）の測定
- 複雑度が高いメソッドをリストアップ
- リファクタリング計画を策定

**ツール**:
- `radon` または `mccabe` を使用

**実行コマンド**:
```bash
uv run radon cc docgen/ -a
```

#### タスク6.2: メソッドの分割
**作業内容**:
- 複雑なメソッドを小さな関数に分割
- ヘルパーメソッドの抽出
- 可読性の向上

**完了基準**:
- [ ] 主要なメソッドの複雑度が削減された
- [ ] コードの可読性が向上した
- [ ] テストが容易になった

---

## 実行順序と依存関係

### 推奨実行順序

1. **フェーズ1: インポートパスの改善** (最優先)
   - 他のフェーズの基盤となる
   - テスト環境の整備に必要

2. **フェーズ2: 例外処理の標準化** (高優先度)
   - コード品質の基盤
   - 他のフェーズでのエラーハンドリングに影響

3. **フェーズ3: コード重複の削減** (中優先度)
   - フェーズ1, 2完了後に実施
   - 保守性の向上に直結

4. **フェーズ4: 統一ファイルスキャナーの統合** (中優先度)
   - フェーズ1完了後に実施可能
   - パフォーマンス改善が期待できる

5. **フェーズ5: 型ヒントの追加** (中優先度)
   - 他のフェーズと並行実施可能
   - 段階的な改善が可能

6. **フェーズ6: メソッドの複雑度削減** (低優先度)
   - 他のフェーズ完了後に実施
   - 継続的な改善として実施

### 依存関係図

```
フェーズ1 (インポート)
    ↓
フェーズ2 (例外処理) ──→ フェーズ3 (重複削減)
    ↓                        ↓
フェーズ4 (ファイルスキャナー)  フェーズ5 (型ヒント)
    ↓                        ↓
    フェーズ6 (複雑度削減)
```

## リスク管理

### リスク1: 既存機能への影響
**対策**:
- 各フェーズで十分なテストを実施
- 段階的なリリース
- ロールバック計画の準備

### リスク2: テストの失敗
**対策**:
- リファクタリング前にテストスイートを確認
- 各フェーズでテストを更新
- CI/CDパイプラインでの自動検証

### リスク3: パフォーマンスの劣化
**対策**:
- ベンチマークテストの実施
- パフォーマンスプロファイリング
- 改善前後の比較

## 検証方法

### 各フェーズの検証

1. **ユニットテスト**
   ```bash
   uv run pytest tests/unit/ -v
   ```

2. **統合テスト**
   ```bash
   uv run pytest tests/integration/ -v
   ```

3. **型チェック**
   ```bash
   uv run mypy docgen/ --ignore-missing-imports
   ```

4. **リンター**
   ```bash
   uv run ruff check docgen/
   ```

5. **フォーマッター**
   ```bash
   uv run ruff format docgen/
   ```

### 完了基準

- [ ] すべてのテストが正常に実行できる
- [ ] 型チェッカーでエラーが発生しない
- [ ] リンターで警告が発生しない
- [ ] 既存の機能に影響がない
- [ ] パフォーマンスが維持または改善されている
- [ ] コードレビューが完了している

## タイムライン（目安）

- **フェーズ1**: 2-3日
- **フェーズ2**: 2-3日
- **フェーズ3**: 3-5日
- **フェーズ4**: 3-5日
- **フェーズ5**: 2-4日（並行実施可能）
- **フェーズ6**: 継続的（優先度低）

**合計**: 約2-3週間（並行作業を考慮）

## 今後のメンテナンス

### 定期的なチェック

1. **コードレビュー**
   - 新しいコードがリファクタリング方針に従っているか確認

2. **技術的負債の監視**
   - 定期的なコード品質チェック
   - 複雑度の監視

3. **パフォーマンス監視**
   - ベンチマークテストの定期実行
   - パフォーマンスの劣化を早期発見

### 予防策

1. **CI/CDパイプラインの強化**
   - 型チェックの自動化
   - 複雑度チェックの追加
   - コードカバレッジの監視

2. **開発ガイドライン**
   - コーディング規約の明確化
   - リファクタリングガイドラインの作成

---

**注意**: この計画を実行する前に、必ずバックアップを取得し、各フェーズを慎重に実行してください。各フェーズの完了後、十分なテストを実施してから次のフェーズに進んでください。

