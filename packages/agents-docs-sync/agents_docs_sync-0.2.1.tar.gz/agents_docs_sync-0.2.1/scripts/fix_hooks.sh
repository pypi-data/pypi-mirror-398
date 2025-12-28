#!/bin/bash
#
# 既存のフックファイルを修正するスクリプト
# シェバンが先頭行にない場合に修正します
#

set -e

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$PROJECT_ROOT" ]; then
    echo "エラー: Gitリポジトリ内で実行してください"
    exit 1
fi

cd "$PROJECT_ROOT"

GIT_HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

fix_hook() {
    local hook_file="$GIT_HOOKS_DIR/$1"

    if [ ! -f "$hook_file" ]; then
        return 0
    fi

    # シェバンが先頭行にない場合、修正する
    if ! head -1 "$hook_file" | grep -q "^#!"; then
        echo "修正中: $hook_file"
        # 一時ファイルを作成
        TEMP_FILE=$(mktemp)

        # シェバンを先頭に追加
        echo "#!/bin/bash" > "$TEMP_FILE"

        # 既存の内容を追加（空行とコメントをスキップ）
        grep -v "^# docgen" "$hook_file" | sed '/^$/d' | sed '1{/^#!/d}' >> "$TEMP_FILE" || true

        # 元のファイルをバックアップ
        cp "$hook_file" "${hook_file}.backup.$(date +%Y%m%d_%H%M%S)"

        # 修正したファイルをコピー
        cp "$TEMP_FILE" "$hook_file"
        rm "$TEMP_FILE"

        chmod +x "$hook_file"
        echo "✓ $hook_file を修正しました"
    else
        echo "✓ $hook_file は既に正しい形式です"
    fi
}

echo "フックファイルを修正中..."
fix_hook "pre-commit"
fix_hook "post-commit"
fix_hook "pre-push"

echo ""
echo "修正完了！"

