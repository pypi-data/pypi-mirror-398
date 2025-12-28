#!/bin/bash
set -e

echo "=== テスト実行開始 ==="

# 仮想環境の確認（オプション）
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 言語検出を実行
echo "言語検出中..."
DETECTED_LANGS=$(PYTHONPATH=. python3 -c "
from docgen.language_detector import LanguageDetector
from pathlib import Path
detector = LanguageDetector(Path('.'))
langs = detector.detect_languages()
print(' '.join([lang.name for lang in langs]))
" 2>/dev/null | tail -1)
if [ -z "$DETECTED_LANGS" ]; then
    echo "言語検出失敗、デフォルトでPythonテストを実行"
    DETECTED_LANGS="python"
fi
echo "検出された言語: $DETECTED_LANGS"

# 言語ごとにテスト実行
for lang in $DETECTED_LANGS; do
    case $lang in
        python)
            echo "Pythonテスト実行中..."
            uv run pytest tests/ -v --tb=short
            ;;
        javascript)
            if [ -f "package.json" ]; then
                echo "JavaScriptテスト実行中..."
                npm test
            else
                echo "package.jsonが見つからないため、JavaScriptテストをスキップ"
            fi
            ;;
        go)
            if [ -f "go.mod" ]; then
                echo "Goテスト実行中..."
                go test ./...
            else
                echo "go.modが見つからないため、Goテストをスキップ"
            fi
            ;;
        generic)
            echo "Generic言語はテストをスキップ"
            ;;
        *)
            echo "不明な言語: $lang - スキップ"
            ;;
    esac
done

echo "=== テスト実行完了 ==="

