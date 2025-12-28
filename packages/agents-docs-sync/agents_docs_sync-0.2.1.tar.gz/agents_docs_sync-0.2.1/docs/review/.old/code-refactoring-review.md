# コード共通化レビュー: agents_generator.py と readme_generator.py

## 概要

`base_generator.py` を参照し、`agents_generator.py` と `readme_generator.py` で共通化できるコードを分析した結果、以下の共通化が可能であると判断しました。

## 共通化可能なメソッド

### 1. `_generate_llm_setup_section`
- **現状**: `base_generator.py` と `agents_generator.py` に重複実装
- **問題**: `readme_generator.py` には実装なし
- **提案**: `base_generator.py` の実装を共通化し、両方のサブクラスで使用可能にする
- **影響**: コード重複の除去、保守性の向上

### 2. `_generate_pr_section`
- **現状**: 両方のファイルでほぼ同じ実装
- **問題**: コード重複
- **提案**: `base_generator.py` に共通実装を追加
- **影響**: プルリクエスト手順の統一、変更時の修正箇所削減

### 3. `_generate_custom_instructions_section`
- **現状**: 両方のファイルで同じ実装
- **問題**: コード重複
- **提案**: `base_generator.py` に共通実装を追加
- **影響**: カスタム指示セクションの統一

### 4. `_generate_coding_standards_section`
- **現状**: 似た実装だがフォーマットが異なる
- **問題**: ロジックは同じだが表示形式が異なる
- **提案**: 共通のロジックを `base_generator.py` に抽出し、表示形式をサブクラスでカスタマイズ
- **影響**: ロジックの重複除去、表示の一貫性向上

### 5. `_generate_setup_section`
- **現状**: 似た実装だが、AGENTS用とREADME用で内容が異なる
- **問題**: 依存関係インストール部分が共通化可能
- **提案**: 依存関係インストールの共通ロジックを `base_generator.py` に抽出し、前提条件部分をサブクラスで実装
- **影響**: インストール手順の統一

### 6. `_generate_build_test_section`
- **現状**: 似た実装だが、uv run の処理などが異なる
- **問題**: コマンドフォーマット処理が重複
- **提案**: `format_commands_with_package_manager` のようなユーティリティ関数を共通化
- **影響**: コマンド処理の一貫性向上

## 実装提案

### 優先度: 高
1. `_generate_llm_setup_section` の共通化
2. `_generate_pr_section` の共通化
3. `_generate_custom_instructions_section` の共通化

### 優先度: 中
4. `_generate_coding_standards_section` のロジック共通化
5. `_generate_setup_section` の依存関係部分共通化

### 優先度: 低
6. `_generate_build_test_section` のユーティリティ共通化

## 利点
- コード重複の削減
- 保守性の向上
- 機能追加時の修正箇所削減
- 各ジェネレーター間の一貫性確保

## 注意点
- 各サブクラスの特殊な要件を維持しながら共通化を行う
- テストを徹底的に実施
- 既存の出力フォーマットを変更しない