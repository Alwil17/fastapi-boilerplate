# 🚀 FastAPI Boilerplate - Clean Architecture

[![Use this template](https://img.shields.io/badge/Use%20this-Template-2ea44f?style=for-the-badge&logo=github)](https://github.com/Alwil17/fastapi-boilerplate/generate)

![CI](https://github.com/Alwil17/fastapi-boilerplate/workflows/CI/badge.svg)
![Python](https://img.shields.io/badge/python-3.13+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)
![Codecov](https://codecov.io/gh/Alwil17/fastapi-boilerplate/branch/master/graph/badge.svg)
![Template checkbox](https://docs.github.com/assets/cb-24935/images/help/repository/template-repository-checkbox.png)

> A production-ready FastAPI boilerplate with clean architecture, JWT authentication, and PostgreSQL/SQLite support.

## ✨ Features

- 🏗️ **Clean Architecture** - Layered structure (API/Services/Repositories/Models)
- 🔐 **JWT Authentication** - Complete auth system with refresh tokens
- 🗄️ **Database Support** - PostgreSQL for production, SQLite for testing
- 🔄 **Alembic Migrations** - Database schema versioning
- 🧪 **Testing Suite** - Pytest with fixtures and mocks
- 🐳 **Docker Ready** - Multi-stage non-root image, gunicorn, compose stack, CD to GHCR
- 📝 **API Documentation** - Auto-generated with Swagger UI
- ⚙️ **Configuration Management** - Pydantic Settings for env variables
- 🔒 **Security Best Practices** - bcrypt, rotating hashed refresh tokens with reuse detection, roles (RBAC), rate limiting, security headers, trusted hosts, fail-fast production config
- 🔭 **Observability** - JSON logs with request ids, one error format, Prometheus metrics, optional Sentry
- 🚦 **CI/CD** - Lint, mypy, tests on Postgres (coverage gate), Bandit, pip-audit, migration drift check, image smoke test and Trivy scan, Dependabot

## 📂 Project Structure

```
fastapi-boilerplate/
├── app/
│   ├── api/
│   │   └── routes/          # API endpoints
│   ├── core/                # Configuration & security
│   ├── db/
│   │   └── models/          # SQLAlchemy models
│   ├── repositories/        # Data access layer
│   ├── services/            # Business logic
│   └── schemas/             # Pydantic models (DTOs)
├── alembic/                 # Database migrations
├── tests/                   # Test suite
├── .env.example             # Environment variables template
├── docker/                  # Entrypoint (migrations), healthcheck, smoke test
├── Dockerfile               # Multi-stage, non-root image
├── docker-compose.yml       # Production-shaped stack (+ .override.yml for dev)
├── gunicorn.conf.py         # Production server settings
├── requirements.in          # Direct dependencies (requirements.txt = hashed lock)
└── requirements.txt         # Pinned runtime dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- PostgreSQL (or use SQLite for local dev)
- pip or poetry

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Alwil17/fastapi-boilerplate.git
   cd fastapi-boilerplate
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install --require-hashes -r requirements-dev.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the server**
   ```bash
   uvicorn app.main:app --reload
   ```

7. **Access the API**
   - API:  http://localhost:8000
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 🐳 Docker Deployment

The image is multi-stage and small (~75 MB): hashed dependencies in a virtualenv, read-only code owned by root, runs as non-root (uid 10001) under gunicorn with uvicorn workers, and has a `HEALTHCHECK` on `/health/live`. On start the entrypoint runs `alembic upgrade head` (retrying while the database comes up).

```bash
cp .env.example .env     # set APP_ENV, APP_SECRET_KEY, DB_PASSWORD, CORS_ORIGINS, ...

# Development: reload on code change, database published on 127.0.0.1 only
docker compose up -d --build

# Production-shaped (skips docker-compose.override.yml): read-only root fs, no DB port
docker compose -f docker-compose.yml up -d --build
```

`docker-compose.yml` has no credentials: everything comes from `.env`, and `DB_PASSWORD` is required. With `APP_ENV=production` the app refuses to start on an unsafe config (default secret, `*` CORS, default DB password, debug on).

Run the image alone (e.g. against a managed database):

```bash
docker build -t fastapi-boilerplate .
docker run -p 8000:8000 --env-file .env fastapi-boilerplate
docker/smoke-test.sh fastapi-boilerplate   # boots it on a throwaway Postgres and checks it
```

| Variable | Default | Purpose |
|---|---|---|
| `WEB_CONCURRENCY` | `2` | gunicorn workers. Each has its own DB pool: connections ≤ workers × (`DB_POOL_SIZE` + `DB_MAX_OVERFLOW`) |
| `FORWARDED_ALLOW_IPS` | `127.0.0.1,::1` | proxies trusted to set `X-Forwarded-For`/`-Proto`. Behind a load balancer set its address/network, otherwise every client appears with the proxy's IP and shares one rate-limit bucket |
| `RUN_MIGRATIONS` | `true` | `false` to skip `alembic upgrade head` at start |
| `GUNICORN_TIMEOUT` / `GUNICORN_GRACEFUL_TIMEOUT` | `30` / `30` | worker kill delay / time to finish in-flight requests on SIGTERM (keep the orchestrator's stop grace period above it) |
| `GUNICORN_MAX_REQUESTS` | `0` | recycle a worker after N requests (0 = never) |

Things to know when scaling out:
- **Migrations**: with several replicas starting together, set `RUN_MIGRATIONS=false` and run `alembic upgrade head` once (one-off job / init container).
- **Rate limiting**: the default `memory://` storage is per worker, so the effective limit is multiplied by the worker count. Use a shared store (`RATE_LIMIT_STORAGE_URI=redis://...`, which needs the `redis` package: add it to `requirements.in`).
- **Host check**: if `ALLOWED_HOSTS` is restricted, orchestrator probes must send an allowed `Host` header (the image's own `HEALTHCHECK` already does).
- **Releases**: pushing a tag `vX.Y.Z` (matching `app.__version__`) runs CI and publishes `ghcr.io/<owner>/<repo>:X.Y.Z`, `X.Y`, `X`.

## 🔐 Dependencies

`requirements.in` / `requirements-dev.in` list direct dependencies; `requirements.txt` / `requirements-dev.txt` are generated with hashes for Python 3.13 (`make lock`, needs [uv](https://docs.astral.sh/uv/)) and installed with `pip install --require-hashes`. To upgrade, run `uv pip compile ... --upgrade` (or `make lock` after editing the `.in` file) and commit the result. `pip-audit` checks the pins in CI.

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with the coverage gate used in CI (fails under 95%)
make test

# Type check
mypy app/

# Run specific test file
pytest tests/test_auth.py -v
```

Load test a running API (k6 in Docker): `make loadtest BASE_URL=http://host.docker.internal:8000`, see [loadtest/api.js](loadtest/api.js).

## 🛟 Operations and security

- [docs/RUNBOOK.md](docs/RUNBOOK.md) - deploy, roll back, health checks, tracing a request, common incidents, routine jobs.
- [SECURITY.md](SECURITY.md) - reporting a vulnerability and the production hardening checklist.

## 📖 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/token` - Login (get access JWT + opaque refresh token)
- `POST /auth/refresh` - Rotate the refresh token (single use) and get a new access token
- `POST /auth/logout` - Revoke a refresh token and its whole family
- `POST /auth/logout-all` - Revoke every refresh token of the current user
- `GET /auth/me` - Get current user info

### Users
- `GET /users?skip=0&limit=50` - List users (admin only)

### Health Check
- `GET /health/live` - Liveness
- `GET /health/ready` - Readiness (checks the database)
- `GET /health` - API health status
- `GET /` - Welcome message
- `GET /metrics` - Prometheus metrics (only when `PROMETHEUS_ENABLED=true`)

## 🔧 Configuration

Key environment variables (see `.env.example`):

```env
# Application
APP_NAME="FastAPI Boilerplate"
APP_ENV=development
APP_SECRET_KEY=your-secret-key

# Database
DB_ENGINE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mydb
DB_USER=user
DB_PASSWORD=password

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Rate limiting (per client IP; use redis://host:6379 when running several workers)
RATE_LIMIT_STORAGE_URI=memory://
RATE_LIMIT_LOGIN=10/minute
```

### Auth and security notes
- Access tokens are short-lived JWTs (`sub` = user id, `iss`/`aud`/`jti`/`type` checked). The role is read from the database on each request, so demotion is immediate.
- Refresh tokens are opaque, stored only as SHA-256 hashes and single use. Replaying a rotated token revokes the whole login family.
- Passwords: 8 to 72 bytes (bcrypt limit). Emails are case-insensitive.
- Create the first admin: `ADMIN_PASSWORD=... python -m app.jobs.create_admin admin@example.com`.
- Purge expired refresh tokens on a schedule: `python -m app.jobs.purge_refresh_tokens`.
- Behind a reverse proxy, set `FORWARDED_ALLOW_IPS` to the proxy address so rate limiting sees real client IPs.
- Known limit: `POST /auth/register` reveals whether an email is taken; fixing that needs an email verification flow.

## 🔭 Observability

- **Logs**: one JSON object per line on stdout (`LOG_FORMAT=json`, default; `console` for local reading), level from `LOG_LEVEL`. Uvicorn logs go through the same pipeline; its own access log is silenced in favour of the app's. Every line carries the `request_id`. Query strings are never logged.
- **Request id**: each response has an `X-Request-ID` header. A well-formed inbound one (`[A-Za-z0-9._-]`, 1-64 chars) is reused so ids can be traced across services; anything else is replaced.
- **Errors**: every non-2xx response has the same shape. Validation errors add `details` (field `loc`, `msg`, `type`; submitted values are never echoed). Unhandled exceptions return a generic 500: the cause is only in the logs and Sentry.

  ```json
  {"error": {"code": "unauthorized", "message": "Not authenticated", "request_id": "9f1c..."}}
  ```

  Codes: `bad_request`, `unauthorized`, `forbidden`, `not_found`, `method_not_allowed`, `conflict`, `validation_error`, `rate_limited`, `internal_error`, `service_unavailable`, else `http_<status>`.
- **Metrics**: `PROMETHEUS_ENABLED=true` serves `GET /metrics` (`http_requests_total`, `http_request_duration_seconds`, `http_requests_in_progress`), labelled by route template so cardinality stays bounded. Do not expose it publicly: restrict it at the proxy/network level and/or set `METRICS_TOKEN` (clients then send `Authorization: Bearer <token>`). Under the Docker image's gunicorn, samples of all workers are aggregated (`PROMETHEUS_MULTIPROC_DIR`, handled by `gunicorn.conf.py`); when running several plain uvicorn processes yourself, counters are per process.
- **Sentry**: set `SENTRY_DSN` to report unhandled exceptions, tagged with the request id. Request bodies, headers, cookies, query strings and local variables are not collected (auth frames hold plaintext passwords).
- **Version**: single source in `app/__version__`, used by the API, OpenAPI, Sentry release and `pyproject.toml`.

## 🏗️ Architecture Principles

This boilerplate follows:

- **Clean Architecture** - Separation of concerns
- **Repository Pattern** - Abstract data access
- **Dependency Injection** - Loose coupling
- **SOLID Principles** - Maintainable code
- **DTOs with Pydantic** - Type safety and validation

## 📚 Tech Stack

- **FastAPI** - Modern web framework
- **SQLAlchemy** - ORM for database operations
- **Alembic** - Database migrations
- **Pydantic** - Data validation
- **JWT** - Authentication
- **Pytest** - Testing framework
- **PostgreSQL** - Production database
- **SQLite** - Testing database

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- Inspired by clean architecture principles
- Built with FastAPI best practices
- Community-driven development

---

**Made with ❤️ by [Alwil17](https://github.com/Alwil17)**
```
