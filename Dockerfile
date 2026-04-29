# syntax=docker/dockerfile:1
FROM python:3.12-slim

# uvのバイナリをコピー
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 環境変数の設定（ログ出力をバッファリングしない）
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# ---------------------------------------------------------
# 1. System dependencies
# ---------------------------------------------------------
COPY packages.txt .
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y $(cat packages.txt) \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------
# 2. Python dependencies (uv cacheを活用)
#    --mount=type=cache を使うことで、リビルド時もダウンロード済みのパッケージを再利用
# ---------------------------------------------------------
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -r requirements.txt

# ---------------------------------------------------------
# 3. PaddleOCR model (モデルデータは重いのでアプリコードの前に配置)
# ---------------------------------------------------------
# ここは一度ダウンロードされれば、repo_idが変わらない限りキャッシュされます
RUN mkdir -p models/japan && \
    python - << 'EOF'
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="PaddlePaddle/PP-OCRv5_mobile_rec",
    local_dir="models/japan/v5_mobile",
    local_dir_use_symlinks=False
)
EOF

# ---------------------------------------------------------
# 4. Application code (一番頻繁に変更される部分)
# ---------------------------------------------------------
COPY . .

EXPOSE 7860

CMD ["streamlit", "run", "app.py", "--server.port", "7860", "--server.address", "0.0.0.0"]