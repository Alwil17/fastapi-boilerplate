# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed
- **Breaking:** all error responses now use `{"error": {"code", "message", "request_id"[, "details"]}}` instead of FastAPI's `{"detail": ...}`.
- Version lives in `app/__version__` (no more `APP_VERSION` setting).

### Added
- Structured JSON logging (`LOG_LEVEL`, `LOG_FORMAT`) with request id and access log.
- `X-Request-ID` header, generated or propagated.
- Optional Prometheus metrics (`PROMETHEUS_ENABLED`, `METRICS_TOKEN`).
- Optional Sentry reporting (`SENTRY_DSN`, `SENTRY_TRACES_SAMPLE_RATE`).

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
