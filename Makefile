.PHONY: help install lock dev test lint format clean docker-build docker-up docker-prod docker-down migrate loadtest

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:   ## Install pinned dependencies (runtime + dev tools)
	pip install --require-hashes -r requirements-dev.txt

lock:  ## Re-resolve requirements*.txt from requirements*.in (needs uv)
	uv pip compile requirements.in -o requirements.txt --universal --python-version 3.13 --generate-hashes --no-header
	uv pip compile requirements-dev.in -o requirements-dev.txt --universal --python-version 3.13 --generate-hashes --no-header

dev:  ## Run development server
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:  ## Run tests with the coverage gate used in CI
	pytest --cov=app --cov-fail-under=95 tests/

lint:  ## Run linting
	ruff check app/ tests/
	mypy app/

format:   ## Format code
	black app/ tests/
	isort app/ tests/

clean:  ## Clean cache files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov

docker-build:  ## Build the production image
	docker build -t fastapi-boilerplate:latest .

docker-up:  ## Start the development stack (compose + override: reload, DB on localhost)
	docker compose up -d --build

docker-prod:  ## Start the production-shaped stack (no override)
	docker compose -f docker-compose.yml up -d --build

docker-down:  ## Stop Docker containers (keeps the database volume)
	docker compose down

BASE_URL ?= http://host.docker.internal:8000
VUS ?= 20
DURATION ?= 30s

loadtest:  ## Load test a running API with k6 in Docker (BASE_URL, VUS, DURATION)
	docker run --rm -i --add-host=host.docker.internal:host-gateway \
		-e BASE_URL=$(BASE_URL) -e VUS=$(VUS) -e DURATION=$(DURATION) \
		grafana/k6 run - < loadtest/api.js

migrate:  ## Run database migrations
	alembic upgrade head

migrate-create:  ## Create new migration
	alembic revision --autogenerate -m "$(msg)"

security:  ## Run security checks
	bandit -r app/ -c pyproject.toml
	pip-audit -r requirements.txt

pre-commit:  ## Run pre-commit hooks
	pre-commit run --all-files

pre-commit-install:  ## Install pre-commit hooks
	pre-commit install

pre-commit-update:  ## Update pre-commit hooks
	pre-commit autoupdate
