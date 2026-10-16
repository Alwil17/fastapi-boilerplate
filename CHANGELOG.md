# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed
- **Breaking:** all error responses now use `{"error": {"code", "message", "request_id"[, "details"]}}` instead of FastAPI's `{"detail": ...}`.
- Version lives in `app/__version__` (no more `APP_VERSION` setting).
- Python 3.13 is the supported version everywhere (image, CI, lint targets, `requires-python`).
- `safety` replaced by `pip-audit`.
- The root endpoint no longer links to `/docs` when the docs are disabled (production).
- ORM models use typed `Mapped[]` columns; `mypy app/` is clean and runs in CI.
- CI: coverage gate at 95%, tests on Python 3.13 and 3.14, least-privilege token permissions, superseded PR runs cancelled, Codecov upload failures fail the build.

### Added
- Production container: multi-stage non-root image on gunicorn + uvicorn workers, `HEALTHCHECK`, entrypoint that applies migrations (`RUN_MIGRATIONS`), `.dockerignore`, `docker/smoke-test.sh`.
- `docker-compose.yml` without hardcoded credentials (read-only fs, required `DB_PASSWORD`) and a `docker-compose.override.yml` for development.
- Dependencies pinned with hashes (`requirements.in` -> `requirements.txt`, `make lock`).
- Release workflow publishing the image to GHCR on `vX.Y.Z` tags; CI smoke-tests the built image.
- Prometheus metrics aggregated across gunicorn workers.
- Structured JSON logging (`LOG_LEVEL`, `LOG_FORMAT`) with request id and access log.
- `X-Request-ID` header, generated or propagated.
- Optional Prometheus metrics (`PROMETHEUS_ENABLED`, `METRICS_TOKEN`).
- Optional Sentry reporting (`SENTRY_DSN`, `SENTRY_TRACES_SAMPLE_RATE`).
- Trivy scan of the built image in CI, Dependabot (pip, Actions, Docker), CodeQL already weekly.
- `SECURITY.md`, `docs/RUNBOOK.md`, `CODEOWNERS`, issue and pull request templates.
- k6 load test (`make loadtest`, `loadtest/api.js`).
- Tests for the user service, the admin/purge jobs, engine construction and the health endpoints with the database down.

### Fixed
- A JSON list in `CORS_ORIGINS` / `ALLOWED_HOSTS` was rejected at startup.

## [1.0.0] - 2026-01-22

### Added
- Initial FastAPI boilerplate with clean architecture
- JWT authentication (register, login, refresh tokens)
- PostgreSQL and SQLite support
- Alembic migrations setup
- Health check endpoints
- Docker configuration
- Complete test suite with pytest
- Documentation (README, CONTRIBUTING, CODE_OF_CONDUCT)

### Security
- Password hashing with bcrypt
- JWT token validation
- CORS middleware configuration
