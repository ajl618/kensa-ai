# Kensa-AI (検査-AI) - Makefile
# Simplifies Docker-based development and testing

.PHONY: help build test demo validate integration clean logs shell \
        mock-server stop up down report-viewer ollama ollama-start ollama-stop ollama-test

# Default target
help:
	@echo "╔═══════════════════════════════════════════════════════════════╗"
	@echo "║      🔍 Kensa-AI (検査-AI) - Docker Commands                  ║"
	@echo "╚═══════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Build Commands:"
	@echo "  make build          Build all Docker images"
	@echo "  make rebuild        Force rebuild without cache"
	@echo ""
	@echo "Testing Commands:"
	@echo "  make test           Run unit tests (66 tests)"
	@echo "  make integration    Run integration tests (18 tests)"
	@echo "  make validate       Validate installation and dependencies"
	@echo "  make demo           Run demo mode"
	@echo ""
	@echo "Ollama (Local LLM):"
	@echo "  make ollama         Full Ollama test (start, pull, test, stop)"
	@echo "  make ollama-start   Start Ollama container"
	@echo "  make ollama-pull    Pull default model (llama3.2:1b)"
	@echo "  make ollama-test    Run tests against Ollama"
	@echo "  make ollama-stop    Stop Ollama container"
	@echo ""
	@echo "Server Commands:"
	@echo "  make mock-server    Start mock AI server"
	@echo "  make mock-vulnerable Start mock server in vulnerable mode"
	@echo "  make report-viewer  Start report viewer (http://localhost:8081)"
	@echo ""
	@echo "Development Commands:"
	@echo "  make shell          Open shell in container"
	@echo "  make logs           Show container logs"
	@echo "  make clean          Remove containers and images"
	@echo ""
	@echo "Run Commands:"
	@echo "  make run            Run tests against configured target"
	@echo "  make run-basic      Run basic security pack"
	@echo "  make run-full       Run full security pack"
	@echo ""

# Build
build:
	docker-compose build

rebuild:
	docker-compose build --no-cache

# Testing
test:
	docker-compose run --rm test

validate:
	docker-compose run --rm validate

demo:
	docker-compose run --rm demo

integration: mock-server-start
	@echo "Waiting for mock server to be ready..."
	@sleep 3
	docker-compose run --rm integration-test
	@$(MAKE) mock-server-stop

# Mock Server
mock-server:
	docker-compose up mock-server

mock-server-start:
	docker-compose up -d mock-server

mock-server-stop:
	docker-compose stop mock-server

mock-vulnerable:
	MOCK_MODE=vulnerable docker-compose up mock-server

# Report Viewer
report-viewer:
	docker-compose --profile viewer up report-viewer

# Run tests
run:
	docker-compose run --rm kensa-ai-tester

run-basic:
	docker-compose run --rm -e TEST_PACK=basic_security kensa-ai-tester

run-full:
	docker-compose run --rm -e TEST_PACK=full_security kensa-ai-tester

run-openai:
	@if [ -z "$$OPENAI_API_KEY" ]; then \
		echo "Error: OPENAI_API_KEY not set"; \
		exit 1; \
	fi
	docker-compose run --rm \
		-e TARGET_URL=https://api.openai.com/v1/chat/completions \
		-e TARGET_API_KEY=$$OPENAI_API_KEY \
		-e TARGET_MODEL=gpt-4 \
		kensa-ai-tester

# Ollama (Local LLM)
ollama-start:
	docker-compose --profile ollama up -d ollama
	@echo "Waiting for Ollama to start..."
	@sleep 10

ollama-stop:
	docker-compose --profile ollama stop ollama

ollama-pull:
	@echo "Pulling default model (llama3.2:1b)..."
	docker exec ollama-target ollama pull llama3.2:1b

ollama-test: ollama-start
	@echo "Waiting for Ollama to be healthy..."
	@sleep 5
	docker-compose --profile ollama run --rm ollama-test
	@$(MAKE) ollama-stop

ollama: ollama-start ollama-pull ollama-test
	@echo "Ollama tests completed!"

# Development
shell:
	docker-compose run --rm --entrypoint /bin/bash kensa-ai-tester

logs:
	docker-compose logs -f

# Cleanup
clean:
	docker-compose down -v --rmi local
	rm -rf reports/*.json reports/*.html

stop:
	docker-compose stop

up:
	docker-compose up -d mock-server

down:
	docker-compose down

# Quick start - build and run demo
quickstart: build mock-server-start
	@sleep 3
	@$(MAKE) demo
	@$(MAKE) mock-server-stop

# CI pipeline
ci: build test integration
	@echo "CI pipeline completed successfully!"

# Full verification
verify: build validate test integration
	@echo ""
	@echo "═══════════════════════════════════════════════════════════"
	@echo " ✓ All verification steps completed successfully!"
	@echo "═══════════════════════════════════════════════════════════"

# Extended demo with 38 prompts
extended-demo: ollama-start
	@echo "Running extended demo with 38 adversarial prompts..."
	docker-compose --profile ollama run --rm --entrypoint python extended-demo -m kensa_ai.examples.extended_demo

# Local development (without Docker)
dev-setup:
	python -m venv venv
	. venv/bin/activate && pip install -e ".[dev]"
	. venv/bin/activate && pre-commit install

dev-test:
	. venv/bin/activate && pytest tests/ -v

dev-lint:
	. venv/bin/activate && ruff check src/ tests/
	. venv/bin/activate && black --check src/ tests/

dev-format:
	. venv/bin/activate && black src/ tests/
	. venv/bin/activate && ruff check --fix src/ tests/

# Docker Hub publishing (requires login)
docker-login:
	docker login

docker-tag:
	docker tag kensa-ai:latest ajjl618/kensa-ai:latest
	docker tag kensa-ai:latest ajjl618/kensa-ai:0.1.0

docker-push: docker-tag
	docker push ajjl618/kensa-ai:latest
	docker push ajjl618/kensa-ai:0.1.0

publish: build docker-push
	@echo "Published to Docker Hub!"

# Generate documentation
docs-serve:
	@echo "Starting documentation server..."
	python -m http.server 8000 --directory docs/

# Security scan
security-scan:
	@echo "Running Trivy security scan..."
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy image kensa-ai:latest

# Benchmark tests
benchmark:
	docker-compose --profile ollama run --rm --entrypoint python extended-demo -m kensa_ai.examples.extended_demo 2>&1 | tee benchmark_$(shell date +%Y%m%d_%H%M%S).log
