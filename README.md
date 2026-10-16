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
- `POST /auth/token` - Login (get JWT tokens)
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current user info

### Health Check
- `GET /health` - API health status
- `GET /` - Welcome message

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
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=7
```

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
