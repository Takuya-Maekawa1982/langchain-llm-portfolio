FROM python:3.12-slim

# Set shell to bash
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# 1. Added HOME and updated PATH so the 'user' can find installed binaries
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    poppler-utils \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Setup user
RUN useradd -m -u 1000 user
USER user
WORKDIR /home/user/app

# Install dependencies
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy EVERY project folder into the container
COPY --chown=user . .

# 2. Updated CMD syntax for cleaner execution on HF
CMD ["streamlit", "run", "app.py", "--server.port", "7860", "--server.address", "0.0.0.0"]