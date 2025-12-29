# ESXi MCP Server Makefile
# Modern Python with uv, Docker Compose for containerization

.PHONY: help install dev test lint format build run run-dev stop logs clean

# Default target
help: ## Show this help
	@echo "ESXi MCP Server"
	@echo "==============="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ─────────────────────────────────────────────────────────────────────────────
# Development Commands
# ─────────────────────────────────────────────────────────────────────────────

install: ## Install dependencies with uv
	uv sync

dev: ## Install with dev dependencies
	uv sync --all-extras

test: ## Run tests
	uv run pytest

lint: ## Run ruff linter
	uv run ruff check src/

format: ## Format code with ruff
	uv run ruff format src/
	uv run ruff check --fix src/

typecheck: ## Run type checking
	uv run mypy src/

# ─────────────────────────────────────────────────────────────────────────────
# Local Run Commands
# ─────────────────────────────────────────────────────────────────────────────

run-local: ## Run MCP server locally (stdio mode for Claude Desktop)
	uv run esxi-mcp-server

run-local-sse: ## Run MCP server locally with SSE transport
	uv run esxi-mcp-server --transport sse

# ─────────────────────────────────────────────────────────────────────────────
# Docker Commands
# ─────────────────────────────────────────────────────────────────────────────

setup: ## Initial setup - create .env from example
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env from .env.example"; \
		echo "Please edit .env with your vCenter credentials"; \
	else \
		echo ".env already exists"; \
	fi
	@mkdir -p logs

build: ## Build Docker image
	docker compose build esxi-mcp-server

build-dev: ## Build development Docker image
	docker compose build esxi-mcp-server-dev

run: setup ## Run production container
	docker compose --profile prod up -d
	@echo "Waiting for container to start..."
	@sleep 3
	docker compose --profile prod logs --tail=20

run-dev: setup ## Run development container with hot-reload
	docker compose --profile dev up -d
	@echo "Waiting for container to start..."
	@sleep 3
	docker compose --profile dev logs --tail=20

stop: ## Stop all containers
	docker compose --profile prod --profile dev down

restart: stop run ## Restart production container

logs: ## Show container logs
	docker compose --profile prod --profile dev logs -f

logs-prod: ## Show production logs only
	docker compose --profile prod logs -f

logs-dev: ## Show development logs only
	docker compose --profile dev logs -f

shell: ## Open shell in running container
	docker compose --profile prod exec esxi-mcp-server bash || \
	docker compose --profile dev exec esxi-mcp-server-dev bash

status: ## Show container status
	docker compose --profile prod --profile dev ps

health: ## Check container health
	@docker compose --profile prod exec esxi-mcp-server \
		python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080')" \
		&& echo "✅ Health check passed" || echo "❌ Health check failed"

# ─────────────────────────────────────────────────────────────────────────────
# Maintenance Commands
# ─────────────────────────────────────────────────────────────────────────────

clean: ## Remove containers and images
	docker compose --profile prod --profile dev down -v --rmi local
	rm -rf .venv __pycache__ .pytest_cache .ruff_cache

clean-all: clean ## Remove everything including uv cache
	rm -rf .uv

lock: ## Update uv.lock file
	uv lock

update: ## Update dependencies
	uv lock --upgrade
	uv sync

# ─────────────────────────────────────────────────────────────────────────────
# Release Commands
# ─────────────────────────────────────────────────────────────────────────────

build-release: ## Build release package
	uv build

publish-test: ## Publish to TestPyPI
	uv publish --repository testpypi

publish: ## Publish to PyPI
	uv publish
