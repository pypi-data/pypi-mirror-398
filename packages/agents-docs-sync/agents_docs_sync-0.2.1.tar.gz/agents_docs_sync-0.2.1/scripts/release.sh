#!/bin/bash
#
# リリーススクリプト
# バージョン番号を更新し、タグを作成してプッシュします
#

set -e

# プロジェクトルートを取得
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
if [ -z "$PROJECT_ROOT" ]; then
    echo "エラー: Gitリポジトリ内で実行してください"
    exit 1
fi

cd "$PROJECT_ROOT"

# pyproject.tomlのパス
PYPROJECT_TOML="$PROJECT_ROOT/pyproject.toml"

# 現在のバージョンを取得
CURRENT_VERSION=$(grep -E '^version = ' "$PYPROJECT_TOML" | sed -E 's/^version = "([^"]+)"/\1/')

if [ -z "$CURRENT_VERSION" ]; then
    echo "エラー: pyproject.tomlからバージョンを取得できませんでした"
    exit 1
fi

echo "現在のバージョン: $CURRENT_VERSION"

# 新しいバージョンを入力
echo ""
read -p "新しいバージョン番号を入力してください (現在: $CURRENT_VERSION): " NEW_VERSION

if [ -z "$NEW_VERSION" ]; then
    echo "エラー: バージョン番号を入力してください"
    exit 1
fi

# バージョンが同じかチェック
if [ "$NEW_VERSION" = "$CURRENT_VERSION" ]; then
    echo "警告: 新しいバージョンが現在のバージョンと同じです"
    read -p "続行しますか？ (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# バージョン形式の検証（セマンティックバージョニング）
if ! [[ "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9]+)?$ ]]; then
    echo "警告: バージョン形式が正しくない可能性があります（例: 0.1.0, 1.2.3）"
    read -p "続行しますか？ (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# pyproject.tomlのバージョンを更新
VERSION_CHANGED=false
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/^version = \".*\"/version = \"$NEW_VERSION\"/" "$PYPROJECT_TOML"
else
    # Linux
    sed -i "s/^version = \".*\"/version = \"$NEW_VERSION\"/" "$PYPROJECT_TOML"
fi

# バージョンが実際に変更されたか確認
if git diff --quiet "$PYPROJECT_TOML" 2>/dev/null; then
    echo "情報: pyproject.tomlのバージョンは既に $NEW_VERSION です（変更なし）"
    VERSION_CHANGED=false
else
    echo "✓ pyproject.tomlのバージョンを $NEW_VERSION に更新しました"
    VERSION_CHANGED=true
fi

# 変更をコミット
echo ""
read -p "変更をコミットしますか？ (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # pyproject.tomlに変更がある場合は追加
    if [ "$VERSION_CHANGED" = true ]; then
        git add "$PYPROJECT_TOML"
    fi

    # ステージングされている変更を確認
    if git diff --cached --quiet 2>/dev/null && git diff --quiet 2>/dev/null; then
        echo "警告: コミットする変更がありません"
    else
        # ステージングされていない変更がある場合は確認
        if ! git diff --cached --quiet 2>/dev/null || ! git diff --quiet 2>/dev/null; then
            # pre-commitフックが追加したファイルも含める
            git add -u 2>/dev/null || true
        fi

        if git commit -m "Bump version to $NEW_VERSION"; then
            echo "✓ 変更をコミットしました"
        else
            echo "警告: コミットに失敗しました（既にコミット済みの可能性があります）"
        fi
    fi
fi

# タグを作成
TAG_NAME="v$NEW_VERSION"
echo ""
read -p "タグ $TAG_NAME を作成してプッシュしますか？ (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 既存のタグをチェック
    if git rev-parse "$TAG_NAME" >/dev/null 2>&1; then
        echo "警告: タグ $TAG_NAME は既に存在します"
        read -p "上書きしますか？ (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git tag -d "$TAG_NAME" 2>/dev/null || true
            git push origin ":refs/tags/$TAG_NAME" 2>/dev/null || true
        else
            echo "タグの作成をスキップしました"
            exit 0
        fi
    fi

    # タグを作成
    git tag -a "$TAG_NAME" -m "Release version $NEW_VERSION"
    echo "✓ タグ $TAG_NAME を作成しました"

    # タグをプッシュ
    echo ""
    read -p "タグをリモートにプッシュしますか？ (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if git push origin "$TAG_NAME"; then
            echo "✓ タグ $TAG_NAME をプッシュしました"
            echo ""
            echo "GitHub Actionsが自動的にリリースを作成します"
            echo "リリースの進行状況は以下で確認できます:"
            echo "https://github.com/$(git config --get remote.origin.url | sed -E 's/.*github.com[:/]([^/]+\/[^/]+)(\.git)?$/\1/')/actions"
        else
            echo "エラー: タグ $TAG_NAME のプッシュに失敗しました"
            exit 1
        fi
    fi
fi

echo ""
echo "リリース処理が完了しました！"

