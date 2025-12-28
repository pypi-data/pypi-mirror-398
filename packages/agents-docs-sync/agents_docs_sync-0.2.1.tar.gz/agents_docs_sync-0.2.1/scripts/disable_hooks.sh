#!/bin/bash
#
# Gitフックを無効化するスクリプト
#

set -e

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$PROJECT_ROOT" ]; then
    echo "エラー: Gitリポジトリ内で実行してください"
    exit 1
fi

cd "$PROJECT_ROOT"

GIT_HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

disable_hook() {
    local hook_name=$1
    local hook_file="$GIT_HOOKS_DIR/$hook_name"
    local disabled_file="${hook_file}.disabled"

    if [ -f "$hook_file" ]; then
        if grep -q "# docgen" "$hook_file" 2>/dev/null; then
            mv "$hook_file" "$disabled_file"
            echo "✓ $hook_nameフックを無効化しました"
        else
            echo "✓ $hook_nameフックはdocgenフックではありません（無視）"
        fi
    else
        echo "✓ $hook_nameフックは存在しません"
    fi
}

echo "Gitフックを無効化中..."
disable_hook "pre-commit"
disable_hook "post-commit"
disable_hook "pre-push"
disable_hook "commit-msg"

echo ""
echo "無効化完了！"
echo "フックを再度有効化するには: ./scripts/enable_hooks.sh"