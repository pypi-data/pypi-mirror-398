#!/bin/bash
#
# Gitフックを手動でインストールするスクリプト (Orchestrated version)
#

set -e

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$PROJECT_ROOT" ]; then
    echo "エラー: Gitリポジトリ内で実行してください"
    exit 1
fi

cd "$PROJECT_ROOT"

GIT_HOOKS_DIR="$PROJECT_ROOT/.git/hooks"
DOCGEN_DIR="$PROJECT_ROOT/docgen"
HOOKS_CONFIG_SRC="$DOCGEN_DIR/hooks.yaml"

if [ ! -d "$GIT_HOOKS_DIR" ]; then
    mkdir -p "$GIT_HOOKS_DIR"
fi

# hooks.yamlが存在しない場合は作成（サンプルからコピー、またはデフォルト作成）
# ここではdocgen/hooks/hooks.yamlが既に存在することを前提とするが、
# もしユーザーがパッケージとしてインストールしている場合は考慮が必要。
# 開発環境ではリポジトリ内のファイルを使用するため問題ない。

install_hook() {
    local hook_name=$1
    local hook_file="$GIT_HOOKS_DIR/$hook_name"
    local source_file="$DOCGEN_DIR/hooks/$hook_name"

    if [ ! -f "$source_file" ]; then
        echo "警告: $hook_name フックのソースファイルが見つかりません: $source_file"
        return 1
    fi

    # 既存のフックをバックアップ（docgen管理外のもののみ）
    if [ -f "$hook_file" ] && ! grep -q "Orchestrated by docgen" "$hook_file" 2>/dev/null; then
        BACKUP_FILE="${hook_file}.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$hook_file" "$BACKUP_FILE"
        echo "既存の$hook_nameフックをバックアップしました: $BACKUP_FILE"
    fi

    # フックをコピー（シンボリックリンクではなくコピーを使用）
    cp "$source_file" "$hook_file"
    chmod +x "$hook_file"
    echo "✓ $hook_nameフックをインストールしました"
}

echo "Gitフックをインストール中..."
install_hook "pre-commit"
install_hook "commit-msg"
install_hook "pre-push"

echo ""
echo "インストール完了！"
echo ""
echo "設定ファイル: docgen/hooks/hooks.yaml"
echo "使用方法:"
echo "  - pre-commit: テスト実行 -> RAG生成 -> ドキュメント生成 -> ステージング"
echo "  - commit-msg: コミットメッセージ自動生成（空の場合）"
echo "  - pre-push: バージョンチェック -> リリースタグ作成（デフォルト無効）"


