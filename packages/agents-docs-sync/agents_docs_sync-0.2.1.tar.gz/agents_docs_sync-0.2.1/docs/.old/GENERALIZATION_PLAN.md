# RAG・検出ロジック一般化計画

## 概要

現在のコードベースには、特定のプロジェクト（特に「Locus」）や言語（日本語）に依存したハードコードされたロジックが存在します。この計画では、どんなプロジェクトでも使用できるように、これらのロジックを一般化します。

## 現状の問題点

### 1. RAG Service (`docgen/generators/services/rag_service.py`)

#### 問題箇所
- **86行目、179行目**: "Locus"というプロジェクト名がハードコード
  ```python
  if project_name.lower() == "locus":
      query_parts.append("NOT about: geographic location, GPS, mapping, coordinates, geography")
      query_parts.append("IS about: RSS feeds, knowledge management, PKM, personal knowledge")
  ```

- **180-181行目**: Locus固有の説明がハードコード
  ```python
  queries.append("RSS feed knowledge management PKM system")
  queries.append("RSS aggregation personal knowledge management")
  ```

#### 影響
- 他のプロジェクトで使用する際に、Locus固有のロジックが誤って適用される可能性
- プロジェクト名が「locus」の場合のみ特別処理されるため、汎用性が低い

### 2. Document Validator (`docgen/rag/validator.py`)

#### 問題箇所
- **19-44行目**: 技術キーワードが英語と日本語でハードコード
  ```python
  TECHNICAL_KEYWORDS = [
      "function", "class", "method", ...,
      "설정",  # 韓国語のコメント（誤り）
      "関数", "クラス", "メソッド", ...
  ]
  ```

#### 影響
- 多言語対応が不完全（韓国語のコメントが誤っている）
- 言語ごとのキーワードがハードコードされており、設定で変更できない

### 3. プロンプトファイル

#### 問題箇所
- `docgen/prompts/readme_prompts.toml`: 日本語のテンプレートがハードコード
- `docgen/prompts/agents_prompts.toml`: 日本語のテンプレートがハードコード

#### 影響
- 英語圏のプロジェクトで使用する際に、日本語のプロンプトが適用される
- 多言語対応ができない

### 4. デフォルトメッセージ

#### 問題箇所
- `docgen/utils/markdown_utils.py` 76行目: 日本語のデフォルトメッセージ
  ```python
  return "このプロジェクトの説明をここに記述してください。"
  ```

- `docgen/generators/services/rag_service.py` 74行目: 日本語のテンプレートチェック
  ```python
  if "このプロジェクトの説明をここに記述してください" not in description:
  ```

#### 影響
- 英語圏のプロジェクトで使用する際に、日本語のメッセージが表示される

## 一般化計画

### フェーズ1: 設定ファイルベースの一般化

#### 1.1 多言語対応の設定化

**実装内容:**
- `config.toml` に `[general]` セクションを追加し、デフォルト言語を設定可能にする
- プロンプトファイルを言語ごとに分離するか、設定で言語を選択できるようにする

**設定例:**
```toml
[general]
# デフォルト言語（"en", "ja", "ko" など）
default_language = "en"

# プロンプトファイルのパス（言語ごと）
[prompts]
readme_prompts = "docgen/prompts/readme_prompts_{language}.toml"
agents_prompts = "docgen/prompts/agents_prompts_{language}.toml"
```

**変更ファイル:**
- `docgen/config.toml.sample`
- `docgen/prompts/readme_prompts.toml` → `readme_prompts_ja.toml`, `readme_prompts_en.toml`
- `docgen/prompts/agents_prompts.toml` → `agents_prompts_ja.toml`, `agents_prompts_en.toml`
- `docgen/utils/prompt_loader.py`（言語対応を追加）

#### 1.2 技術キーワードの設定化

**実装内容:**
- `config.toml` に技術キーワードの設定を追加
- 言語ごとのキーワードを設定可能にする

**設定例:**
```toml
[validator.technical_keywords]
# デフォルトのキーワード（英語）
default = [
    "function", "class", "method", "module", "package",
    "import", "export", "implements", "extends", "returns",
    "parameter", "argument", "type", "defined", "located", "configured"
]

# 言語ごとの追加キーワード
[validator.technical_keywords.languages]
ja = ["関数", "クラス", "メソッド", "モジュール", "パッケージ", "実装", "定義"]
ko = ["함수", "클래스", "메서드", "모듈", "패키지", "구현", "정의"]
```

**変更ファイル:**
- `docgen/rag/validator.py`
- `docgen/config.toml.sample`

#### 1.3 デフォルトメッセージの多言語化

**実装内容:**
- デフォルトメッセージを設定ファイルまたはリソースファイルに移動
- 言語ごとのメッセージを定義

**設定例:**
```toml
[messages]
# デフォルトのプロジェクト説明メッセージ
default_description = {
    en = "Please describe this project here.",
    ja = "このプロジェクトの説明をここに記述してください。",
    ko = "여기에 프로젝트 설명을 작성하세요."
}
```

**変更ファイル:**
- `docgen/utils/markdown_utils.py`
- `docgen/generators/services/rag_service.py`
- `docgen/config.toml.sample`

### フェーズ2: コードのリファクタリング

#### 2.1 Validator の一般化

**変更内容:**
1. 技術キーワードを設定ファイルから読み込む
2. 言語ごとのキーワードを動的に組み合わせる

**実装例:**
```python
class DocumentValidator:
    def __init__(self, project_root: Path | None = None, config: dict[str, Any] | None = None):
        self.project_root = project_root or Path.cwd()
        self.config = config or {}

        # 設定から技術キーワードを読み込む
        keyword_config = self.config.get("validator", {}).get("technical_keywords", {})
        default_keywords = keyword_config.get("default", [])

        # 言語ごとのキーワードを追加
        language = self.config.get("general", {}).get("default_language", "en")
        language_keywords = keyword_config.get("languages", {}).get(language, [])

        self.TECHNICAL_KEYWORDS = default_keywords + language_keywords
```

**変更ファイル:**
- `docgen/rag/validator.py`

#### 2.2 プロンプトローダーの多言語対応

**変更内容:**
1. 設定ファイルから言語を取得
2. 言語に応じたプロンプトファイルを読み込む

**実装例:**
```python
def load_prompt(prompt_name: str, config: dict[str, Any]) -> str:
    language = config.get("general", {}).get("default_language", "en")
    prompts_config = config.get("prompts", {})

    # プロンプトファイルのパスを取得（言語を考慮）
    prompt_file = prompts_config.get("readme_prompts", "").format(language=language)
    # ... 読み込み処理
```

**変更ファイル:**
- `docgen/utils/prompt_loader.py`

### フェーズ3: テストとドキュメント

#### 3.1 テストの追加

**テスト内容:**
- 多言語対応のテスト
- デフォルトメッセージの多言語化テスト

**追加ファイル:**
- `tests/test_rag_service_generalization.py`
- `tests/test_validator_generalization.py`
- `tests/test_prompt_loader_multilang.py`

#### 3.2 ドキュメントの更新

**更新内容:**
- `docs/CONFIG_GUIDE.md`: 新しい設定項目の説明を追加
- `README.md`: 多言語対応の説明を追加
- `docs/DEVELOPER_GUIDE.md`: 一般化の説明を追加

## 実装の優先順位

### 高優先度（即座に実施）
1. **デフォルトメッセージの多言語化**（フェーズ1.3）
   - ユーザーが最初に目にする部分
   - 実装が比較的簡単

### 中優先度（短期間で実施）
2. **技術キーワードの設定化**（フェーズ1.2, 2.1）
   - 検証機能の改善
   - 多言語対応の拡張

3. **プロンプトファイルの多言語化**（フェーズ1.1, 2.2）
   - より高度な多言語対応
   - 実装がやや複雑

### 低優先度（長期的に実施）
4. **テストとドキュメント**（フェーズ3）
   - 品質保証とメンテナンス性の向上

## 移行戦略

### 後方互換性の維持

1. **デフォルト値の設定**
   - 設定ファイルが存在しない場合、現在のハードコードされた値をデフォルトとして使用
   - 既存のプロジェクトが動作し続けるようにする

2. **段階的な移行**
   - まず設定ファイルのサポートを追加
   - 次にハードコードされた値を設定ファイルから読み込むように変更
   - 最後にハードコードされた値を削除

3. **設定ファイルの自動生成**
   - 既存のプロジェクトに対して、デフォルト設定ファイルを自動生成する機能を追加

## 期待される効果

1. **汎用性の向上**
   - どんなプロジェクトでも使用可能
   - プロジェクト固有のロジックを設定で制御可能

2. **多言語対応**
   - 英語、日本語、韓国語など、複数の言語に対応
   - 言語ごとのカスタマイズが可能

3. **メンテナンス性の向上**
   - ハードコードされた値を削除し、設定ファイルで管理
   - コードの変更なしに動作を調整可能

4. **拡張性の向上**
   - 新しいプロジェクト固有のロジックを簡単に追加可能
   - 新しい言語のサポートを簡単に追加可能

## 実装チェックリスト

### フェーズ1: 設定ファイルベースの一般化
- [ ] `config.toml.sample` に `[general]` セクションを追加
- [ ] `config.toml.sample` に `[validator.technical_keywords]` セクションを追加
- [ ] `config.toml.sample` に `[messages]` セクションを追加
- [ ] プロンプトファイルを言語ごとに分離（`readme_prompts_ja.toml`, `readme_prompts_en.toml` など）
- [ ] 英語版のプロンプトファイルを作成

### フェーズ2: コードのリファクタリング
- [ ] `validator.py` の `DocumentValidator` クラスを一般化
- [ ] `markdown_utils.py` のデフォルトメッセージを多言語化
- [ ] `prompt_loader.py` に多言語対応を追加

### フェーズ3: テストとドキュメント
- [ ] RAG Service の一般化のテストを追加
- [ ] Validator の一般化のテストを追加
- [ ] プロンプトローダーの多言語対応のテストを追加
- [ ] `docs/CONFIG_GUIDE.md` を更新
- [ ] `README.md` を更新
- [ ] `docs/DEVELOPER_GUIDE.md` を更新

## 注意事項

1. **後方互換性**
   - 既存のプロジェクトが動作し続けるように、デフォルト値を適切に設定する
   - 設定ファイルが存在しない場合のフォールバック処理を実装する

2. **パフォーマンス**
   - 設定ファイルの読み込みは起動時に一度だけ行う
   - キャッシュを適切に使用する

3. **エラーハンドリング**
   - 設定ファイルの読み込みエラーを適切に処理する
   - デフォルト値へのフォールバックを実装する

4. **テスト**
   - 各フェーズで十分なテストを追加する
   - 既存のテストが壊れないように注意する

