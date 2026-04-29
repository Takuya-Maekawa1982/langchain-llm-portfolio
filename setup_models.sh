#!/usr/bin/env bash
set -e

echo "=== Downloading Japanese OCR model (PP-OCRv5 mobile) ==="

mkdir -p models/japan

echo "Downloading PP-OCRv5 Ultra Light (mobile)..."
python - << 'EOF'
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="PaddlePaddle/PP-OCRv5_mobile_rec",
    local_dir="models/japan/v5_mobile",
    local_dir_use_symlinks=False
)
EOF

echo "Download completed: PP-OCRv5_mobile_rec"
