# ドキュメント検証改善計画

## 問題の概要

現在、生成されたドキュメント（特にAGENTS.mdやAPIドキュメント）に、実装されていない機能や関数が含まれることがあります。これは以下の原因によるものです：

1. **LLM生成時の実装情報不足**: LLMがドキュメントを生成する際、実際のコードベースから抽出された実装情報を十分に参照していない
2. **生成後の検証不足**: 生成されたドキュメントが実際のコードベースと整合しているかを検証する仕組みがない
3. **APIドキュメントと実装の不整合**: パーサーが抽出したAPI情報と、LLMが生成した説明の間に不整合が生じる可能性

## 改善目標

1. 生成されたドキュメントに実装されていない機能が含まれないようにする
2. ドキュメント生成時に実装情報を確実に参照する
3. 生成後の自動検証により、不整合を早期に発見する
4. 設定可能な検証レベルを提供する

## 改善計画

### フェーズ1: 実装検証機能の追加

#### 1.1 実装検証モジュールの作成

**ファイル**: `docgen/validators/implementation_validator.py`

**機能**:
- ドキュメント内で言及されている関数名、クラス名、メソッド名を抽出
- 実際のコードベース内でそれらが存在するかを検証
- パーサーが抽出したAPI情報と照合
- 検証結果をレポート形式で出力

**実装内容**:
```python
class ImplementationValidator:
    """実装検証クラス"""

    def __init__(self, project_root: Path, parsers: list[BaseParser]):
        self.project_root = project_root
        self.parsers = parsers
        self.implemented_apis = {}  # 実装済みAPIのキャッシュ

    def extract_referenced_entities(self, document: str) -> list[EntityReference]:
        """ドキュメントから参照されているエンティティを抽出"""
        # 関数名、クラス名、メソッド名を抽出
        pass

    def validate_implementation(self, document: str) -> ValidationResult:
        """実装の存在を検証"""
        # 1. 実装済みAPIを収集
        # 2. ドキュメント内の参照を抽出
        # 3. 照合して不一致を検出
        pass

    def build_api_index(self) -> dict:
        """実装済みAPIのインデックスを構築"""
        # パーサーを使用して実装済みAPIを収集
        pass
```

#### 1.2 エンティティ参照抽出の実装

**機能**:
- Markdownドキュメントから関数名、クラス名、メソッド名を抽出
- コードブロック内の参照も検出
- 言語別のパターンマッチング

**実装内容**:
- 正規表現パターンによる抽出
- AST解析（可能な場合）
- 言語別の命名規則に対応

### フェーズ2: LLM生成時の実装情報提供

#### 2.1 プロンプトへの実装情報追加

**ファイル**: `docgen/generators/agents_generator.py` (修正)

**変更内容**:
- LLM生成時に、実装済みAPI情報をプロンプトに含める
- RAGコンテキストに実装情報を追加
- プロンプトテンプレートを更新して実装情報を強調

**実装内容**:
```python
def _create_llm_prompt(self, project_info: ProjectInfo, rag_context: str = "") -> str:
    # 実装済みAPI情報を取得
    api_info = self._get_implemented_api_info(project_info)

    # プロンプトに実装情報を追加
    prompt = PromptLoader.load_prompt(
        "agents_prompts.toml",
        "full_with_rag",
        config=self.config,
        project_info=self._format_project_info_for_prompt(project_info),
        rag_context=rag_context,
        implemented_apis=api_info,  # 新規追加
    )
    return prompt

def _get_implemented_api_info(self, project_info: ProjectInfo) -> str:
    """実装済みAPI情報を取得"""
    # APIジェネレーターを使用して実装済みAPIを収集
    # ただし、ドキュメント生成は行わず、情報のみを返す
    pass
```

#### 2.2 プロンプトテンプレートの更新

**ファイル**: `docgen/prompts/agents_prompts.toml` (修正)

**変更内容**:
- 実装済みAPI情報を参照する指示を追加
- 実装されていない機能を記載しないよう明示的に指示

**例**:
```toml
[prompts]
full_with_rag = """
以下のプロジェクト情報を基に、AIコーディングエージェント向けのAGENTS.mdドキュメントを生成してください。

{project_info}

実装済みAPI情報:
{implemented_apis}

重要:
- 実装済みAPI情報に記載されている機能のみを記載してください
- 実装されていない機能や関数を記載しないでください
- 推測や仮定に基づく記述は避けてください

{rag_context}
"""
```

### フェーズ3: 生成後の自動検証

#### 3.1 検証ステップの統合

**ファイル**: `docgen/generators/base_generator.py` (修正)

**変更内容**:
- `generate()` メソッドに検証ステップを追加
- 検証失敗時の処理を実装

**実装内容**:
```python
def generate(self) -> bool:
    """ドキュメントを生成"""
    try:
        # ... 既存の生成ロジック ...

        # 生成後の検証
        if self.config.get("validation", {}).get("enabled", True):
            validation_result = self._validate_generated_document(markdown)
            if not validation_result["valid"]:
                self.logger.error("生成されたドキュメントの検証に失敗しました")
                if self.config.get("validation", {}).get("strict", False):
                    return False
                else:
                    self.logger.warning("警告モード: 検証エラーがあっても続行します")
                    self._print_validation_report(validation_result)

        # ... 既存の書き込みロジック ...

    except Exception as e:
        # ... エラーハンドリング ...
```

#### 3.2 検証レポートの出力

**機能**:
- 検証結果を構造化されたレポートとして出力
- エラーと警告を分類
- 修正提案を含める

### フェーズ4: 設定と統合

#### 4.1 設定ファイルの拡張

**ファイル**: `docgen/config.toml.sample` (修正)

**追加設定**:
```toml
[validation]
enabled = true  # 検証を有効化
strict = false  # 厳格モード（検証失敗時に生成を中断）
check_implementation = true  # 実装検証を有効化
check_citations = true  # 出典検証を有効化
warn_on_missing = true  # 実装されていない参照を警告

[validation.implementation]
# 実装検証の詳細設定
exclude_patterns = ["test_", "_test", "mock_"]  # 除外パターン
include_private = false  # プライベートメソッドを含めるか
```

#### 4.2 CLI統合

**ファイル**: `docgen/cli/commands/generate.py` (修正)

**変更内容**:
- `--validate` オプションの追加
- `--strict-validation` オプションの追加
- 検証結果の表示

#### 4.3 フック統合

**ファイル**: `docgen/hooks/orchestrator.py` (修正)

**変更内容**:
- ドキュメント生成後の自動検証を追加
- 検証失敗時の警告/エラー処理

## 実装の優先順位

### 高優先度（フェーズ1-2）
1. 実装検証モジュールの作成
2. LLM生成時の実装情報提供
3. 基本的な検証機能の統合

### 中優先度（フェーズ3）
1. 生成後の自動検証
2. 検証レポートの出力
3. 設定ファイルの拡張

### 低優先度（フェーズ4）
1. CLI統合の拡張
2. フック統合の拡張
3. 詳細な検証オプション

## 期待される効果

1. **ドキュメントの正確性向上**: 実装されていない機能が記載されることがなくなる
2. **開発効率の向上**: 不正確なドキュメントによる混乱を防止
3. **信頼性の向上**: ドキュメントと実装の整合性が保証される
4. **自動化の強化**: 検証が自動化され、手動チェックが不要になる

## リスクと対策

### リスク1: 検証の誤検出
**対策**:
- 除外パターンの設定を柔軟に
- 警告モードとエラーモードの選択可能に
- 検証結果の詳細なログ出力

### リスク2: パフォーマンスへの影響
**対策**:
- API情報のキャッシュ機能
- 並列処理の活用
- 検証のスキップオプション

### リスク3: 既存ワークフローへの影響
**対策**:
- デフォルトで警告モード（strict=false）
- 段階的な導入
- 後方互換性の維持

## テスト計画

1. **単体テスト**: 各検証モジュールのテスト
2. **統合テスト**: ドキュメント生成と検証の統合テスト
3. **回帰テスト**: 既存機能への影響を確認
4. **パフォーマンステスト**: 大規模プロジェクトでの検証速度

## 今後の拡張

1. **複数言語対応**: 言語別の検証ルール
2. **カスタム検証ルール**: プロジェクト固有の検証ルール定義
3. **CI/CD統合**: 検証結果をCI/CDパイプラインに統合
4. **レポート形式の拡張**: HTML、JSON形式のレポート出力

