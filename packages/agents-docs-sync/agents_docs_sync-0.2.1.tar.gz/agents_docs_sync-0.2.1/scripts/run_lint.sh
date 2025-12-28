#!/bin/bash
# Lintチェックスクリプト

set -e

echo "Running ruff linter..."
ruff check .

echo "Lint check passed!"