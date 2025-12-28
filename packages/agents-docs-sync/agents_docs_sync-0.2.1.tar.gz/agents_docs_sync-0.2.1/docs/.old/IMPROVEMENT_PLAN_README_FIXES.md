# README生成問題の汎用的対処計画

## 概要

Locusプロジェクトで発見されたREADME.md生成の問題を、すべてのプロジェクトに適用できる汎用的な解決策として実装する計画です。

## 発見された問題点

### 1. プロジェクト説明の収集順序の問題
- **現状**: README.mdが優先的に参照され、古い説明が使用される
- **影響**: `package.json`や`pyproject.toml`の正しい説明が無視される

### 2. アーキテクチャ図の言語タイプ誤検出
- **現状**: 複数言語が検出された場合、優先順位が適切に適用されない
- **影響**: 誤った言語タイプでアーキテクチャ図が生成される

### 3. Servicesセクションの重複と誤情報
- **現状**: 同じ名前で異なるタイプのサービスが重複して検出される
- **影響**: 誤った情報がREADME.mdに含まれる

### 4. 依存関係の誤検出
- **現状**: プロジェクト名やツール名が依存関係として検出される
- **影響**: 不要な依存関係が表示される

### 5. アーキテクチャ図のコンテンツ取得時のフィルタリング不足
- **現状**: Servicesセクションがそのまま含まれる
- **影響**: 誤った情報がREADME.mdに含まれる

## 実装計画

### Phase 1: プロジェクト説明の収集順序改善

#### 1.1 自動優先順位決定ロジックの実装
- 検出された言語とパッケージマネージャから自動的に優先順位を決定
- パッケージマネージャファイルの存在を確認して優先順位を決定
  - `package.json`が存在 → `package.json`を最優先
  - `pyproject.toml`が存在 → `pyproject.toml`を最優先
  - `setup.py`が存在 → `setup.py`を優先
  - 上記が存在しない場合のみ`README.md`を参照
- パッケージマネージャの検出結果を活用（`LanguageDetector`から取得）

#### 1.2 `LanguageInfoCollector`の改善
- `collect_project_description()`を修正
- 検出された言語・パッケージマネージャに基づいた自動収集順序を実装
- README.mdの説明を検証（デフォルトメッセージやテンプレートテキストを除外）
- パッケージマネージャ情報を`ProjectInfoCollector`から取得

#### 1.3 `extract_project_description()`の改善
- `markdown_utils.py`の関数を修正
- 検出された言語・パッケージマネージャに基づいた自動優先順位を実装
- より厳密な検証ロジックを追加
- デフォルトメッセージやテンプレートテキストを自動検出して除外

**実装ファイル**:
- `docgen/collectors/language_info_collector.py`
- `docgen/utils/markdown_utils.py`
- `docgen/collectors/project_info_collector.py`（パッケージマネージャ情報の取得）

### Phase 2: アーキテクチャスキャン時のサービス重複除去と優先順位付け

#### 2.1 `ArchitectureManifest`の改善
- サービス重複除去メソッドを追加
- 言語優先順位（`languages.preferred`設定）に基づいたサービス選択ロジックを実装
- より詳細な情報（モジュール、依存関係）を持つサービスを優先
- 同じ名前で異なるタイプのサービスが検出された場合、優先言語に基づいて選択

#### 2.2 `ProjectScanner`の改善
- スキャン後にサービスを自動的に正規化
- 重複除去と優先順位付けを常に実行（設定不要）
- `languages.preferred`設定を参照して優先順位を決定
- 検出された言語リストから主要言語を自動判定

**実装ファイル**:
- `docgen/archgen/models.py`
- `docgen/archgen/scanner.py`

### Phase 3: 依存関係の検証とフィルタリング

#### 3.1 依存関係フィルタリングロジックの追加
- プロジェクト名を自動的に除外
- 既存の`exclude.directories`設定を参照して除外パターンを構築
- `languages.ignored`設定を参照して除外パターンを構築
- ツール名（agents-docs-sync、docgen等）を自動検出して除外
- プロジェクトルートのディレクトリ名を除外パターンとして使用

#### 3.2 自動除外ロジックの実装
- `exclude.directories`の各ディレクトリ名を依存関係から除外
- プロジェクト名（`project_root.name`）を依存関係から除外
- 設定ファイルの読み込み時に除外パターンを自動構築

**実装ファイル**:
- `docgen/archgen/detectors/generic_detector.py`
- `docgen/archgen/detectors/python_detector.py`
- `docgen/archgen/models.py`
- `docgen/archgen/scanner.py`（除外パターンの構築）

### Phase 4: アーキテクチャ図のコンテンツ取得時のフィルタリング

#### 4.1 `_get_architecture_diagram_content()`の改善
- アーキテクチャ図のMarkdownからServicesセクションのみを抽出
- Mermaid図のコードブロックとServicesセクションを分離
- ServicesセクションのみをREADME.mdに含める（設定不要、常に適用）

**実装ファイル**:
- `docgen/generators/base_generator.py`

### Phase 5: 言語優先順位の活用

#### 5.1 アーキテクチャ図生成時の言語判定改善
- `languages.preferred`設定を活用
- 主要言語に基づいたサービス選択を実装

#### 5.2 MermaidGeneratorの改善
- 言語優先順位に基づいたアイコン選択
- 主要言語に基づいたスタイル適用

**実装ファイル**:
- `docgen/archgen/generators/mermaid_generator.py`
- `docgen/archgen/renderer.py`

### Phase 6: サービス説明の検証と改善

#### 6.1 サービス説明の自動検証と改善
- デフォルト説明（"Add your description here"、"Add your description"等）を自動検出
- デフォルト説明が検出された場合、自動的に`package.json`や`pyproject.toml`から説明を取得
- 説明が空の場合も同様にメタデータから自動取得
- 警告はログに記録（設定不要、常に適用）

**実装ファイル**:
- `docgen/archgen/detectors/generic_detector.py`
- `docgen/archgen/detectors/python_detector.py`
- `docgen/archgen/scanner.py`

## 実装順序

1. **Phase 1**: プロジェクト説明の収集順序改善（最優先）
2. **Phase 3**: 依存関係の検証とフィルタリング
3. **Phase 2**: アーキテクチャスキャン時のサービス重複除去
4. **Phase 4**: アーキテクチャ図のコンテンツ取得時のフィルタリング
5. **Phase 5**: 言語優先順位の活用
6. **Phase 6**: サービス説明の検証と改善

## テスト計画

### 単体テスト
- 各フェーズの機能を個別にテスト
- 設定の読み込みと適用をテスト

### 統合テスト
- Locusプロジェクトでの動作確認
- 他のプロジェクト（agents-docs-sync等）での動作確認
- 複数言語プロジェクトでの動作確認

### 回帰テスト
- 既存のプロジェクトで問題が発生しないことを確認

## 互換性

- 既存の設定ファイルは後方互換性を維持
- 新しい設定項目は追加しない（自動判定・処理のみ）
- 既存の設定（`languages.preferred`、`languages.ignored`、`exclude.directories`）を活用
- デフォルト動作は既存の動作を維持しつつ、自動的に改善

## ドキュメント更新

- `docs/DEVELOPER_GUIDE.md`に実装詳細を追加（自動判定ロジックの説明）
- 変更履歴を`CHANGELOG.md`に記録
- 既存の設定項目（`languages.preferred`、`languages.ignored`、`exclude.directories`）の活用方法を明記

## 完了条件

- [ ] すべてのフェーズが実装されている
- [ ] 単体テストと統合テストが通過している
- [ ] Locusプロジェクトで正しいREADME.mdが生成される
- [ ] 他のプロジェクトで問題が発生しないことを確認
- [ ] ドキュメントが更新されている

