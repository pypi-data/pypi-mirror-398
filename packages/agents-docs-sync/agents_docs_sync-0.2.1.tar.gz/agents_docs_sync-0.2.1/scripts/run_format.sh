#!/bin/bash
# Formatスクリプト

set -e

echo "Running ruff formatter..."
ruff format .

echo "Code formatting completed!"