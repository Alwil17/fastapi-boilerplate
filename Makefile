.PHONY: help install lock dev test lint format clean docker-up docker-down migrate

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

test:  ## Run tests
	pytest -v --cov=app tests/

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

docker-up:  ## Start Docker containers
	docker-compose up -d

docker-down:  ## Stop Docker containers
	docker-compose down

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
