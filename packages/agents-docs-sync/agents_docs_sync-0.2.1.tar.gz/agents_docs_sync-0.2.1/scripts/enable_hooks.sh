#!/bin/bash
#
# Gitフックを有効化するスクリプト
#

set -e

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$PROJECT_ROOT" ]; then
    echo "エラー: Gitリポジトリ内で実行してください"
    exit 1
fi

cd "$PROJECT_ROOT"

GIT_HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

enable_hook() {
    local hook_name=$1
    local hook_file="$GIT_HOOKS_DIR/$hook_name"
    local disabled_file="${hook_file}.disabled"

    if [ -f "$disabled_file" ]; then
        mv "$disabled_file" "$hook_file"
        chmod +x "$hook_file"
        echo "✓ $hook_nameフックを有効化しました"
    else
        echo "✓ $hook_nameフックは既に有効化されています"
    fi
}

echo "Gitフックを有効化中..."
enable_hook "pre-commit"
enable_hook "post-commit"
enable_hook "pre-push"
enable_hook "commit-msg"

echo ""
echo "有効化完了！"
echo "フックを無効化するには: ./scripts/disable_hooks.sh"