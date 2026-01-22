# 📖 FastAPI Boilerplate - Complete Usage Guide

## Table of Contents
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Database Management](#database-management)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

- **Python 3.11+**
- **PostgreSQL 12+** (or use SQLite for development)
- **Docker & Docker Compose** (optional but recommended)
- **Git**

### Quick Setup

#### Option 1: Local Development

```bash
# 1. Clone the repository
git clone https://github.com/Alwil17/fastapi-boilerplate.git
cd fastapi-boilerplate

# 2. Create virtual environment
python -m venv . venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev. txt

# 4. Setup pre-commit hooks
pre-commit install

# 5. Configure environment
cp .env.example .env
# Edit .env with your configuration

# 6. Initialize database
alembic upgrade head

# 7. Run the application
uvicorn app.main:app --reload
```

#### Option 2: Docker Development

```bash
# 1. Clone the repository
git clone https://github.com/Alwil17/fastapi-boilerplate. git
cd fastapi-boilerplate

# 2. Start all services
docker-compose up -d

# 3. View logs
docker-compose logs -f api

# 4. Access the API
# http://localhost:8000
```

### Verify Installation

```bash
# Check API health
curl http://localhost:8000/health

# Access Swagger UI
open http://localhost:8000/docs
```

---

## Project Structure

```
fastapi-boilerplate/
│
├── app/                          # Main application code
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry point
│   │
│   ├── api/                      # API layer
│   │   ├── __init__.py
│   │   └── routes/               # API endpoints
│   │       ├── __init__.py
│   │       ├── auth_routes.py    # Authentication endpoints
│   │       └── health_routes.py  # Health check endpoints
│   │
│   ├── core/                     # Core configuration
│   │   ├── __init__.py
│   │   ├── config.py             # Application settings
│   │   ├── config_test.py        # Test configuration
│   │   └── security.py           # JWT & password hashing
│   │
│   ├── db/                       # Database layer
│   │   ├── __init__.py
│   │   ├── base.py               # Database setup & session
│   │   └── models/               # SQLAlchemy ORM models
│   │       ├── __init__.py
│   │       ├── base.py           # Base model class
│   │       ├── user.py           # User model
│   │       └── refresh_token.py  # RefreshToken model
│   │
│   ├── repositories/             # Data access layer
│   │   ├── __init__.py
│   │   ├── user_repository.py    # User CRUD operations
│   │   └── refresh_token_repository.py
│   │
│   ├── services/                 # Business logic layer
│   │   ├── __init__.py
│   │   └── user_service.py       # User business logic
│   │
│   └── schemas/                  # Pydantic models (DTOs)
│       ├── __init__.py
│       ├── user_dto.py           # User data transfer objects
│       └── auth_dto.py           # Authentication DTOs
│
├── alembic/                      # Database migrations
│   ├── versions/                 # Migration files
│   ├── env.py                    # Alembic configuration
│   └── script.py. mako            # Migration template
│
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── conftest.py               # Pytest fixtures
│   ├── test_auth.py              # Authentication tests
│   └── test_health.py            # Health check tests
│
├── docs/                         # Documentation
│   ├── USAGE_GUIDE.md            # This file
│   └── ARCHITECTURE.md           # Architecture documentation
│
├── .github/                      # GitHub configuration
│   └── workflows/                # CI/CD pipelines
│       ├── ci.yml                # Main CI pipeline
│       └── security.yml          # Security scanning
│
├── .env. example                  # Environment variables template
├── .env.test                     # Test environment variables
├── .gitignore                    # Git ignore rules
├── . pre-commit-config.yaml       # Pre-commit hooks config
├── alembic.ini                   # Alembic configuration
├── bandit.yaml                   # Bandit security config
├── docker-compose.yml            # Docker Compose configuration
├── Dockerfile                    # Docker image definition
├── Makefile                      # Development commands
├── pyproject.toml                # Python project configuration
├── pytest.ini                    # Pytest configuration
├── requirements.txt              # Production dependencies
├── requirements-dev. txt          # Development dependencies
├── README.md                     # Project overview
├── LICENSE                       # MIT License
├── CODE_OF_CONDUCT.md            # Code of conduct
└─�� CONTRIBUTING.md               # Contribution guidelines
```

---

## Development Workflow

### Using Makefile Commands

The Makefile provides convenient shortcuts for common tasks:

```bash
# Show all available commands
make help

# Development
make install              # Install all dependencies
make dev                  # Run development server with auto-reload

# Code Quality
make lint                 # Run all linting tools (ruff, mypy)
make format               # Format code with black and isort
make security             # Run security checks (bandit, safety)

# Testing
make test                 # Run tests with coverage

# Pre-commit
make pre-commit-install   # Install pre-commit hooks
make pre-commit           # Run pre-commit hooks manually

# Docker
make docker-up            # Start Docker services
make docker-down          # Stop Docker services

# Database
make migrate              # Apply database migrations
make migrate-create msg="description"  # Create new migration

# Cleanup
make clean                # Remove cache files
```

### Code Quality Tools

#### **Black** - Code Formatter

Automatically formats Python code to conform to PEP 8.

```bash
# Format all code
black app/ tests/

# Check without modifying
black --check app/ tests/

# Format specific file
black app/main.py
```

**Configuration** (in `pyproject.toml`):
- Line length: 88 characters
- Target Python version: 3.11

#### **isort** - Import Sorter

Organizes and sorts import statements. 

```bash
# Sort imports
isort app/ tests/

# Check without modifying
isort --check-only app/ tests/

# Show differences
isort --diff app/
```

**Import Order**:
1. Standard library imports
2. Third-party imports
3. First-party imports (app. *)
4. Local imports

#### **Ruff** - Fast Python Linter

A fast Python linter written in Rust, replacing Flake8, pylint, and more.

```bash
# Check for issues
ruff check app/ tests/

# Auto-fix issues
ruff check --fix app/ tests/

# Show all violations
ruff check app/ --output-format=full
```

**What Ruff Checks**:
- Syntax errors (E, W)
- Undefined names (F)
- Import order (I)
- Comprehension improvements (C)
- Bug-prone patterns (B)
- Modern Python upgrades (UP)

#### **MyPy** - Type Checker

Static type checker for Python.

```bash
# Check types
mypy app/

# Check specific module
mypy app/services/user_service.py

# Generate HTML report
mypy app/ --html-report mypy-report
```

**Best Practices**:
```python
# Good:  Type hints for function parameters and return
def get_user(user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

# Good: Type hints for variables
name: str = "John"
age: int = 30
```

#### **Bandit** - Security Linter

Finds common security issues in Python code.

```bash
# Run security scan
bandit -r app/ -c pyproject.toml

# Generate detailed report
bandit -r app/ -f json -o bandit-report.json
```

**Common Issues Detected**:
- SQL injection vulnerabilities
- Use of insecure functions
- Hardcoded passwords
- Shell injection risks

#### **Safety** - Dependency Scanner

Checks for known security vulnerabilities in dependencies.

```bash
# Check dependencies
safety check --file requirements.txt

# Generate JSON report
safety check --json --file requirements.txt
```

### Pre-commit Hooks

Pre-commit hooks run automatically before each commit to ensure code quality.

#### Setup

```bash
# Install hooks
pre-commit install

# Update hooks to latest versions
pre-commit autoupdate
```

#### Usage

```bash
# Hooks run automatically on git commit
git add .
git commit -m "your message"

# Run manually on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files

# Skip hooks (not recommended)
git commit -m "message" --no-verify
```

#### What Pre-commit Checks

1. **Trailing whitespace** - Removes trailing spaces
2. **End of file fixer** - Ensures files end with newline
3. **YAML/JSON/TOML checker** - Validates syntax
4. **Large files detector** - Prevents committing large files
5. **Merge conflict detector** - Detects merge conflict markers
6. **Private key detector** - Prevents committing private keys
7. **Black** - Formats code
8. **isort** - Sorts imports
9. **Ruff** - Lints code
10. **MyPy** - Type checks
11. **Bandit** - Security scan

### Git Workflow

#### Branch Naming Convention

```bash
# Features
git checkout -b feat/user-authentication
git checkout -b feat/add-email-verification

# Bug fixes
git checkout -b bugfix/fix-login-error
git checkout -b bugfix/fix-database-connection

# Documentation
git checkout -b docs/update-readme
git checkout -b docs/add-api-examples

# Maintenance
git checkout -b chore/update-dependencies
git checkout -b chore/refactor-user-service
```

#### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Feature
git commit -m "feat:  add user registration endpoint"

# Bug fix
git commit -m "fix: resolve token expiration issue"

# Documentation
git commit -m "docs: update installation guide"

# Refactoring
git commit -m "refactor: improve database query performance"

# Tests
git commit -m "test:  add tests for authentication flow"

# Build/CI
git commit -m "ci: add security scanning workflow"
```

---

## Testing

### Running Tests

#### Basic Usage

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with extra verbose output (show test names)
pytest -vv

# Run specific test file
pytest tests/test_auth.py

# Run specific test function
pytest tests/test_auth. py::test_register_user

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf
```

#### Coverage Reports

```bash
# Run tests with coverage
pytest --cov=app tests/

# Generate HTML coverage report
pytest --cov=app --cov-report=html tests/

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows

# Generate terminal coverage with missing lines
pytest --cov=app --cov-report=term-missing tests/

# Generate XML coverage (for CI/CD)
pytest --cov=app --cov-report=xml tests/
```

### Writing Tests

#### Test Structure

```python
# tests/test_example.py

def test_function_name(client, db_session):
    """Test description of what is being tested."""
    # Arrange - Setup test data
    user_data = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123"
    }
    
    # Act - Execute the code being tested
    response = client.post("/auth/register", json=user_data)
    
    # Assert - Verify the results
    assert response.status_code == 201
    assert response. json()["email"] == user_data["email"]
```

#### Using Fixtures

```python
# tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(db_session):
    """Create a test client."""
    from app.main import app
    from app.db.base import get_db
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
```

#### Test Examples

**Testing Authentication**

```python
def test_register_user(client):
    """Test user registration creates a new user."""
    response = client.post(
        "/auth/register",
        json={
            "name":  "John Doe",
            "email": "john@example.com",
            "password": "securepass123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "john@example.com"
    assert "id" in data
    assert "hashed_password" not in data  # Password should not be returned

def test_login_success(client):
    """Test successful login returns JWT tokens."""
    # First register a user
    client.post(
        "/auth/register",
        json={
            "name":  "Jane Doe",
            "email": "jane@example.com",
            "password": "password123"
        }
    )
    
    # Then login
    response = client.post(
        "/auth/token",
        data={
            "username": "jane@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client):
    """Test login with invalid credentials fails."""
    response = client.post(
        "/auth/token",
        data={
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
```

**Testing Protected Endpoints**

```python
def test_get_current_user(client):
    """Test getting current user info with valid token."""
    # Register and login
    client.post(
        "/auth/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123"
        }
    )
    
    login_response = client.post(
        "/auth/token",
        data={
            "username": "test@example.com",
            "password": "password123"
        }
    )
    token = login_response.json()["access_token"]
    
    # Get current user
    response = client.get(
        "/auth/me",
        headers={"Authorization":  f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"

def test_protected_endpoint_without_token(client):
    """Test protected endpoint without token returns 401."""
    response = client.get("/auth/me")
    assert response.status_code == 401
```

### Mocking

```python
from unittest.mock import Mock, patch

def test_with_mock(client, mocker):
    """Test using mocked external service."""
    # Mock external API call
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "mocked"}
    
    with patch('requests.get', return_value=mock_response):
        response = client.get("/external-api")
        assert response. status_code == 200
```

---

## Database Management

### Alembic Migrations

#### Create Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add user table"

# Create empty migration (manual)
alembic revision -m "Custom migration"
```

#### Apply Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade one version
alembic upgrade +1

# Downgrade one version
alembic downgrade -1

# Downgrade to specific version
alembic downgrade <revision>

# Downgrade all
alembic downgrade base
```

#### View Migration History

```bash
# Show current version
alembic current

# Show migration history
alembic history

# Show migration details
alembic show <revision>
```

#### Migration Best Practices

1. **Always review auto-generated migrations**
   ```python
   # alembic/versions/xxx_add_user_table.py
   
   def upgrade() -> None:
       # Review these operations
       op. create_table('users',
           sa.Column('id', sa.Integer(), nullable=False),
           sa.Column('email', sa.String(length=100), nullable=False),
           sa.PrimaryKeyConstraint('id')
       )
   ```

2. **Test migrations in development first**
   ```bash
   # Test upgrade
   alembic upgrade head
   
   # Test downgrade
   alembic downgrade -1
   
   # Test upgrade again
   alembic upgrade head
   ```

3. **Never edit applied migrations**
   - Create a new migration instead
   - Old migrations should remain unchanged

4. **Write reversible migrations**
   ```python
   def upgrade() -> None:
       op.add_column('users', sa.Column('phone', sa.String(20)))
   
   def downgrade() -> None:
       op. drop_column('users', 'phone')
   ```

### Database Models

#### Creating a New Model

```python
# app/db/models/example.py

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.models.base import Base

class Example(Base):
    __tablename__ = "examples"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Fields
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    
    # Foreign key
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
    
    # Relationships
    user = relationship("User", back_populates="examples")
    
    def __repr__(self):
        return f"<Example(id={self.id}, name='{self.name}')>"
```

#### Register Model

```python
# app/db/models/__init__.py

from .user import User
from .refresh_token import RefreshToken
from .example import Example  # Add new model

__all__ = ["User", "RefreshToken", "Example"]
```

#### Create Migration

```bash
alembic revision --autogenerate -m "Add example table"
alembic upgrade head
```

### Database Queries

#### Repository Pattern

```python
# app/repositories/example_repository.py

from typing import List, Optional
from sqlalchemy. orm import Session
from app.db.models. example import Example

class ExampleRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, name: str, user_id: int) -> Example:
        example = Example(name=name, user_id=user_id)
        self.db.add(example)
        self.db.commit()
        self.db.refresh(example)
        return example
    
    def get_by_id(self, example_id: int) -> Optional[Example]:
        return self.db.query(Example).filter(Example.id == example_id).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Example]:
        return self. db.query(Example).offset(skip).limit(limit).all()
    
    def get_by_user(self, user_id: int) -> List[Example]:
        return self.db.query(Example).filter(Example.user_id == user_id).all()
    
    def update(self, example_id: int, name: str) -> Optional[Example]:
        example = self.get_by_id(example_id)
        if example:
            example.name = name
            self.db.commit()
            self.db.refresh(example)
        return example
    
    def delete(self, example_id: int) -> bool:
        example = self.get_by_id(example_id)
        if example:
            self.db.delete(example)
            self.db.commit()
            return True
        return False
```

---

## API Documentation

### Swagger UI

Access interactive API documentation at: 
```
http://localhost:8000/docs
```

Features:
- Try out API endpoints
- View request/response schemas
- Test authentication
- Download OpenAPI spec

### ReDoc

Alternative documentation interface:
```
http://localhost:8000/redoc
```

Features:
- Clean, readable interface
- Detailed schema information
- Code samples
- Easy navigation

### OpenAPI Spec

Download OpenAPI JSON: 
```
http://localhost:8000/openapi.json
```

### API Testing with cURL

#### Authentication

```bash
# Register a new user
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "securepass123"
  }'

# Login
curl -X POST "http://localhost:8000/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john@example.com&password=securepass123"

# Response: 
# {
#   "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "refresh_token": "a1b2c3d4.. .",
#   "token_type": "bearer"
# }
```

#### Protected Endpoints

```bash
# Get current user (requires authentication)
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Refresh access token
curl -X POST "http://localhost:8000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

#### Health Check

```bash
# Check API health
curl -X GET "http://localhost:8000/health"

# Response:
# {
#   "status": "healthy",
#   "timestamp": "2026-01-22T10:30:00",
#   "database": "healthy",
#   "version": "1.0.0"
# }
```

### API Testing with HTTPie

HTTPie is a user-friendly HTTP client:

```bash
# Install HTTPie
pip install httpie

# Register user
http POST localhost:8000/auth/register \
  name="Jane Doe" \
  email="jane@example.com" \
  password="pass123"

# Login
http POST localhost:8000/auth/token \
  username=jane@example.com \
  password=pass123

# Get current user
http GET localhost:8000/auth/me \
  Authorization:"Bearer YOUR_TOKEN"
```

---

## Deployment

### Environment Variables

#### Development

```env
APP_NAME="FastAPI Boilerplate Dev"
APP_ENV=development
APP_DEBUG=True
APP_SECRET_KEY=dev-secret-key-change-in-production

DB_ENGINE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mydb_dev
DB_USER=dev_user
DB_PASSWORD=dev_password

ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=7
```

#### Production

```env
APP_NAME="FastAPI Boilerplate"
APP_ENV=production
APP_DEBUG=False
APP_SECRET_KEY=your-super-secure-secret-key-min-32-chars

DB_ENGINE=postgresql
DB_HOST=your-production-db-host. com
DB_PORT=5432
DB_NAME=prod_database
DB_USER=prod_user
DB_PASSWORD=very-secure-production-password

ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
```

**Security Checklist**:
- ✅ Change `APP_SECRET_KEY` to a strong random value
- ✅ Set `APP_DEBUG=False` in production
- ✅ Use strong database password
- ✅ Never commit `.env` files
- ✅ Restrict database access by IP
- ✅ Use SSL/TLS for database connections

### Docker Production

#### Optimized Dockerfile

```dockerfile
# Multi-stage build for smaller image
FROM python:3.11-slim as builder

WORKDIR /app

# Install dependencies
COPY requirements.txt . 
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Copy wheels from builder
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

# Install dependencies
RUN pip install --no-cache /wheels/*

# Copy application
COPY ./app ./app
COPY ./alembic ./alembic
COPY ./alembic.ini . 

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Build and Run

```bash
# Build image
docker build -t fastapi-boilerplate: 1.0.0 .

# Run container
docker run -d \
  --name fastapi-app \
  -p 8000:8000 \
  --env-file .env. production \
  fastapi-boilerplate:1.0.0

# View logs
docker logs -f fastapi-app

# Stop container
docker stop fastapi-app
```

### Docker Compose Production

```yaml
version: '3.8'

services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes: 
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test:  ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env.production
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test:  ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx. conf:/etc/nginx/nginx. conf: ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
    restart: unless-stopped

volumes:
  postgres_data:
```

### Cloud Deployment

#### Heroku

```bash
# Install Heroku CLI
brew install heroku/brew/heroku  # macOS
# or download from https://devcenter.heroku.com/articles/heroku-cli

# Login
heroku login

# Create app
heroku create your-app-name

# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Set environment variables
heroku config:set APP_SECRET_KEY=your-secret-key
heroku config:set APP_ENV=production

# Deploy
git push heroku main

# Run migrations
heroku run alembic upgrade head

# View logs
heroku logs --tail
```

#### AWS ECS

1. Create ECR repository
2. Build and push Docker image
3. Create ECS cluster
4. Define task definition
5. Create ECS service
6. Configure load balancer

#### Google Cloud Run

```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/fastapi-boilerplate

# Deploy
gcloud run deploy fastapi-boilerplate \
  --image gcr.io/PROJECT_ID/fastapi-boilerplate \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## Best Practices

### Code Organization

#### Adding New Features

1. **Create Database Model**
   ```python
   # app/db/models/feature.py
   class Feature(Base):
       __tablename__ = "features"
       # Define columns
   ```

2. **Create Schema/DTO**
   ```python
   # app/schemas/feature_dto.py
   class FeatureCreate(BaseModel):
       # Define fields
   ```

3. **Create Repository**
   ```python
   # app/repositories/feature_repository.py
   class FeatureRepository:
       # Define CRUD operations
   ```

4. **Create Service**
   ```python
   # app/services/feature_service.py
   class FeatureService:
       # Define business logic
   ```

5. **Create Routes**
   ```python
   # app/api/routes/feature_routes.py
   router = APIRouter(prefix="/features", tags=["Features"])
   # Define endpoints
   ```

6. **Write Tests**
   ```python
   # tests/test_feature. py
   def test_create_feature(client):
       # Test implementation
   ```

7. **Create Migration**
   ```bash
   alembic revision --autogenerate -m "Add feature table"
   alembic upgrade head
   ```

### Security Best Practices

1. **Environment Variables**
   - Never commit `.env` files
   - Use strong secret keys (min 32 characters)
   - Rotate secrets regularly

2. **Authentication**
   - Use strong password hashing (bcrypt)
   - Implement JWT with short expiration
   - Validate tokens on every request
   - Use refresh tokens

3. **Input Validation**
   - Validate all user inputs with Pydantic
   - Sanitize data before database queries
   - Use parameterized queries (SQLAlchemy handles this)

4. **CORS Configuration**
   ```python
   # Production
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],  # Specific domains
       allow_credentials=True,
       allow_methods=["GET", "POST", "PUT", "DELETE"],
       allow_headers=["*"],
   )
   ```

5. **Rate Limiting**
   ```python
   # Install slowapi
   pip install slowapi
   
   # Add to main.py
   from slowapi import Limiter, _rate_limit_exceeded_handler
   from slowapi.util import get_remote_address
   from slowapi.errors import RateLimitExceeded
   
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
   
   @router.post("/login")
   @limiter.limit("5/minute")
   async def login(request: Request, ... ):
       pass
   ```

### Performance Optimization

1. **Database Queries**
   ```python
   # Use select_related to avoid N+1 queries
   users = db.query(User).options(joinedload(User.refresh_tokens)).all()
   
   # Use pagination
   users = db.query(User).offset(skip).limit(limit).all()
   
   # Add database indexes
   class User(Base):
       email = Column(String, unique=True, index=True)
   ```

2. **Caching**
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=128)
   def get_settings():
       return Settings()
   ```

3. **Async Operations**
   ```python
   # Use async for I/O operations
   @router.get("/users")
   async def get_users():
       # Async database query
       users = await db.execute(select(User))
       return users
   ```

### Code Style

1. **Type Hints**
   ```python
   from typing import List, Optional
   
   def get_users(skip: int = 0, limit: int = 100) -> List[User]:
       return db.query(User).offset(skip).limit(limit).all()
   ```

2. **Docstrings**
   ```python
   def create_user(user_data: UserCreateDTO) -> User:
       """
       Create a new user in the database.
       
       Args:
           user_data: User creation data including name, email, and password
           
       Returns:
           User:  The created user object
           
       Raises:
           ValueError: If user with email already exists
       """
       pass
   ```

3. **Error Handling**
   ```python
   from fastapi import HTTPException, status
   
   if not user: 
       raise HTTPException(
           status_code=status.HTTP_404_NOT_FOUND,
           detail="User not found"
       )
   ```

---

## Troubleshooting

### Common Issues

#### Database Connection Errors

**Problem**: `could not connect to server:  Connection refused`

**Solutions**:
```bash
# Check if PostgreSQL is running
docker-compose ps

# View PostgreSQL logs
docker-compose logs db

# Restart PostgreSQL
docker-compose restart db

# Check environment variables
cat .env | grep DB_
```

#### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'app'`

**Solutions**:
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python path
echo $PYTHONPATH

# Run from project root
cd /path/to/fastapi-boilerplate
python -m pytest
```

#### Migration Conflicts

**Problem**: `Target database is not up to date. `

**Solutions**:
```bash
# View current version
alembic current

# View migration history
alembic history

# Downgrade and upgrade
alembic downgrade -1
alembic upgrade head

# In extreme cases (CAREFUL!)
alembic downgrade base
alembic upgrade head
```

#### Port Already in Use

**Problem**: `Address already in use`

**Solutions**:
```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# Use different port
uvicorn app.main:app --port 8001
```

#### JWT Token Issues

**Problem**: `Could not validate credentials`

**Solutions**:
- Check token expiration
- Verify `APP_SECRET_KEY` matches between encoding and decoding
- Ensure token format:  `Bearer <token>`
- Check token in Swagger UI

```python
# Debug JWT
from jose import jwt
from app.core.config import settings

token = "your-token-here"
try:
    payload = jwt.decode(token, settings.APP_SECRET_KEY, algorithms=["HS256"])
    print(payload)
except Exception as e: 
    print(f"Error: {e}")
```

#### Pre-commit Hook Failures

**Problem**: Pre-commit hooks failing

**Solutions**:
```bash
# Update hooks
pre-commit autoupdate

# Clear cache
pre-commit clean

# Reinstall hooks
pre-commit uninstall
pre-commit install

# Skip hooks temporarily (not recommended)
git commit --no-verify
```

### Debug Mode

Enable detailed logging: 

```python
# app/main.py
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.get("/debug")
async def debug():
    logger.debug("Debug information")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    return {"debug": "enabled"}
```

### Getting Help

1. **Check Documentation**
   - [FastAPI Docs](https://fastapi.tiangolo.com/)
   - [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
   - [Pydantic Docs](https://docs.pydantic.dev/)

2. **Search Issues**
   - [GitHub Issues](https://github.com/Alwil17/fastapi-boilerplate/issues)

3. **Ask for Help**
   - Open a new issue with: 
     - Clear problem description
     - Steps to reproduce
     - Expected vs actual behavior
     - Environment details (OS, Python version, etc.)
     - Error messages and logs

---

## Additional Resources

### Official Documentation

- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [SQLAlchemy](https://docs.sqlalchemy.org/) - ORM
- [Alembic](https://alembic.sqlalchemy.org/) - Database migrations
- [Pytest](https://docs.pytest.org/) - Testing framework

### Tutorials

- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [SQLAlchemy Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)
- [JWT Authentication](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)

### Tools

- [Postman](https://www.postman.com/) - API testing
- [DBeaver](https://dbeaver.io/) - Database management
- [HTTPie](https://httpie.io/) - CLI HTTP client

---

**Need help? ** [Open an issue](https://github.com/Alwil17/fastapi-boilerplate/issues) or check [CONTRIBUTING.md](../CONTRIBUTING.md)

**Made with ❤️ by [Alwil17](https://github.com/Alwil17)**
