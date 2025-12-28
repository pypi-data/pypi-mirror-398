# agents-docs-sync Dockerイメージ
FROM python:3.12-slim

# メタデータ
LABEL maintainer="agents-docs-sync contributors"
LABEL description="GitHubにプッシュされた変更をトリガーに、テスト実行・ドキュメント生成・AGENTS.mdの自動更新を行うパイプライン"

# 作業ディレクトリを設定
WORKDIR /app

# システム依存関係のインストール（必要に応じて）
RUN apt-get update && apt-get install -y \
    git \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係のインストール
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir build wheel setuptools && \
    pip install --no-cache-dir pyyaml>=6.0.3

# アプリケーションコードをコピー
COPY . .

# パッケージをインストール
RUN pip install --no-cache-dir -e .

# エントリーポイントを設定
ENTRYPOINT ["agents-docs-sync"]

# デフォルトコマンド（ヘルプを表示）
CMD ["--help"]

