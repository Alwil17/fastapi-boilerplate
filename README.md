# 🚀 FastAPI Boilerplate - Clean Architecture

[![Use this template](https://img.shields.io/badge/Use%20this-Template-2ea44f?style=for-the-badge&logo=github)](https://github.com/Alwil17/fastapi-boilerplate/generate)

![CI](https://github.com/Alwil17/fastapi-boilerplate/workflows/CI/badge.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)
![Codecov](https://codecov.io/gh/Alwil17/fastapi-boilerplate/branch/master/graph/badge.svg)
![Template checkbox](https://docs.github.com/assets/cb-24935/images/help/repository/template-repository-checkbox.png)

> A production-ready FastAPI boilerplate with clean architecture, JWT authentication, and PostgreSQL/SQLite support.

## ✨ Features

- 🏗️ **Clean Architecture** - Layered structure (API/Services/Repositories/Models)
- 🔐 **JWT Authentication** - Complete auth system with refresh tokens
- 🗄️ **Database Support** - PostgreSQL for production, SQLite for testing
- 🔄 **Alembic Migrations** - Database schema versioning
- 🧪 **Testing Suite** - Pytest with fixtures and mocks
- 🐳 **Docker Ready** - Dockerfile included
- 📝 **API Documentation** - Auto-generated with Swagger UI
- ⚙️ **Configuration Management** - Pydantic Settings for env variables
- 🔒 **Security Best Practices** - Password hashing, CORS, JWT validation

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
├── Dockerfile               # Docker configuration
└── requirements.txt         # Python dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
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
   pip install -r requirements.txt
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

```bash
# Build the image
docker build -t fastapi-boilerplate .

# Run the container
docker run -p 8000:8000 --env-file .env fastapi-boilerplate
```

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_auth.py -v
```

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

- **Logs**: one JSON object per line on stdout (`LOG_FORMAT=json`, default; `console` for local reading), level from `LOG_LEVEL`. Uvicorn logs go through the same pipeline; its own access log is replaced by the app's, so run it without relying on `--access-log`. Every line carries the `request_id`. Query strings are never logged.
- **Request id**: each response has an `X-Request-ID` header. A well-formed inbound one (`[A-Za-z0-9._-]`, 1-64 chars) is reused so ids can be traced across services; anything else is replaced.
- **Errors**: every non-2xx response has the same shape. Validation errors add `details` (field `loc`, `msg`, `type`; submitted values are never echoed). Unhandled exceptions return a generic 500: the cause is only in the logs and Sentry.

  ```json
  {"error": {"code": "unauthorized", "message": "Not authenticated", "request_id": "9f1c..."}}
  ```

  Codes: `bad_request`, `unauthorized`, `forbidden`, `not_found`, `method_not_allowed`, `conflict`, `validation_error`, `rate_limited`, `internal_error`, `service_unavailable`, else `http_<status>`.
- **Metrics**: `PROMETHEUS_ENABLED=true` serves `GET /metrics` (`http_requests_total`, `http_request_duration_seconds`, `http_requests_in_progress`), labelled by route template so cardinality stays bounded. Do not expose it publicly: restrict it at the proxy/network level and/or set `METRICS_TOKEN` (clients then send `Authorization: Bearer <token>`). Counters are per process: with several workers, scrape each one or use prometheus_client's multiprocess mode.
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
