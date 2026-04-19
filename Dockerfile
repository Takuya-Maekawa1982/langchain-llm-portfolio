FROM python:3.12-slim

# Set shell to bash with pipefail for better error handling
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install Poppler without a specific version pin to avoid Debian repo mismatches
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    poppler-utils \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Setup user
RUN useradd -m -u 1000 user
USER user
WORKDIR /home/user/app

# Install all requirements from root
COPY --chown=user requirements.txt .
# Use --user to avoid permission issues and keep it within the home dir
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy EVERY project folder into the container
COPY --chown=user . .

# Run the Router app
CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]