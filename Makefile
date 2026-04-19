# Variables
	IMAGE_NAME = takuya-ai-toolbox
	PROJECT_NAME ?= bill-extractor-ai
HADOLINT_PATH = /home/coder/go/bin/hadolint
BIN_DIR = /home/coder/go/bin


.PHONY: build clean prune lint install-hadolint

# 1. Build
build:
	docker build --build-arg PROJECT_NAME=$(PROJECT_NAME) -t $(IMAGE_NAME) .

# 2. Install Hadolint with Directory Check
install-hadolint:
	@mkdir -p $(BIN_DIR)
	curl -L https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-x86_64 -o $(HADOLINT_PATH)
	chmod +x $(HADOLINT_PATH)

# 3. Lint (with a check to see if hadolint exists first)
lint:
	@if [ ! -f $(HADOLINT_PATH) ]; then $(MAKE) install-hadolint; fi
	$(HADOLINT_PATH) Dockerfile

# 4. Remove image
clean:
	docker rmi $(IMAGE_NAME) || echo "Image already gone."

# 5. Save Disk Space (Critical for local dev)
prune:
	docker system prune -f

# 6. Run the Container (Production-style)
run:
	docker run -p 8501:8501 --env-file .env $(IMAGE_NAME)

# 7. Development Mode (Live-reload: Changes in VS Code show up instantly)
dev:
	docker run -p 8501:8501 --env-file .env -v "$(shell pwd):/app" $(IMAGE_NAME)