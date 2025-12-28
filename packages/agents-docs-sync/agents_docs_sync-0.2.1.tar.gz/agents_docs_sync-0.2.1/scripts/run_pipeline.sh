#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== 統合パイプライン開始 ==="

# ステップ1: テスト実行
echo "[1/3] テスト実行中..."
"$SCRIPT_DIR/run_tests.sh"
if [ $? -ne 0 ]; then
    echo "エラー: テストが失敗しました"
    exit 1
fi

# ステップ2: ドキュメント生成
echo "[2/3] ドキュメント生成中..."
cd "$PROJECT_ROOT"
python3 docgen/docgen.py
if [ $? -ne 0 ]; then
    echo "エラー: ドキュメント生成が失敗しました"
    exit 1
fi

# ステップ3: 完了
echo "[3/3] パイプライン完了"
echo "=== 統合パイプライン終了 ==="

