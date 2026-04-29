# ==========================================
# 1. Configuration
# ==========================================
IMAGE_NAME = takuya-ai-toolbox
VENV = .venv_3_12
LOG_DIR = logs
LOG_FILE = $(LOG_DIR)/app.log

# Platform Detection
ifeq ($(OS),Windows_NT)
    PYTHON_SYS := python
    BIN := $(VENV)/Scripts
    # Windowsでは明示的に .exe をつける
    PYTHON_VENV := $(BIN)/python.exe
    MKDIR := mkdir -p
    RM := rm -rf
    TEE := 
else
    PYTHON_SYS := python3
    BIN := $(VENV)/bin
    # Linux/Macは .exe 不要
    PYTHON_VENV := $(BIN)/python
    MKDIR := mkdir -p
    RM := rm -rf
    TEE := | tee $(LOG_FILE)
endif

# Cloud Paths
HADOLINT_PATH = /home/coder/go/bin/hadolint
BIN_DIR = /home/coder/go/bin

# System Level Tool Check
UV := $(shell command -v uv 2> /dev/null)

export PYTHONUNBUFFERED=1

.PHONY: venv sync run-local logs-local build lint prune clean test models help

# ==========================================
# 2. Infrastructure & Dependencies (SoC)
# ==========================================

venv:
ifndef UV
	$(error "uv is not installed. Install via: curl -LsSf https://astral.sh/uv/install.sh | sh")
endif
	@echo ">>> [STEP 1/2] Creating virtual environment: $(VENV)"
	uv venv $(VENV) --python $(PYTHON_SYS)

sync:
	@if [ ! -d "$(VENV)" ]; then $(MAKE) venv; fi
	@echo ">>> [STEP 2/2] Syncing libraries via uv"
	# 確定したパスを指定
	uv pip install -r requirements.txt --python $(PYTHON_VENV)
# ==========================================
# 3. Runtime & Logging
# ==========================================

run-local:
	@$(MKDIR) $(LOG_DIR)
	@echo ">>> Starting Streamlit app (Local mode)..."
	$(BIN)/streamlit run app.py --server.port 8501 $(TEE)

logs-local:
	@if [ ! -f $(LOG_FILE) ]; then echo "No log file found."; exit 1; fi
	tail -f $(LOG_FILE)

# ==========================================
# 4. QA & Docker Operations
# ==========================================

build:
	@echo ">>> Building Docker image: $(IMAGE_NAME)"
	docker build -t $(IMAGE_NAME) .

lint:
	@echo ">>> Running Hadolint..."
	@if [ ! -f $(HADOLINT_PATH) ]; then \
		$(MKDIR) $(BIN_DIR); \
		curl -L https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-x86_64 -o $(HADOLINT_PATH); \
		chmod +x $(HADOLINT_PATH); \
	fi
	$(HADOLINT_PATH) Dockerfile

test:
	@echo ">>> Running tests..."
	$(BIN)/pytest -s tests/test_app.py

prune:
	docker system prune -f

# ==========================================
# 5. Utilities (修正済: 最もシンプルな clean)
# ==========================================

models:
	@echo ">>> Setting up models..."
	bash setup_models.sh

clean:
	@echo ">>> Cleaning up environment and logs..."
	$(RM) $(VENV)
	$(RM) $(LOG_DIR)

help:
	@echo "Usage: make [target]"
	@echo "  venv        : Create venv"
	@echo "  sync        : Sync dependencies"
	@echo "  run-local   : Run locally"
	@echo "  test        : Run pytest"
	@echo "  lint        : Run hadolint"
	@echo "  models      : Run setup_models.sh"
	@echo "  clean       : Remove venv and logs"