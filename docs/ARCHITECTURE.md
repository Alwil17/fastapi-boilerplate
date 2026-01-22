# 🏗️ Architecture Documentation

## Overview

This FastAPI boilerplate follows **Clean Architecture** principles, emphasizing separation of concerns, testability, and maintainability. 

## Table of Contents

- [Architecture Principles](#architecture-principles)
- [Layer Architecture](#layer-architecture)
- [Data Flow](#data-flow)
- [Design Patterns](#design-patterns)
- [Security Architecture](#security-architecture)
- [Database Design](#database-design)
- [Testing Strategy](#testing-strategy)
- [Scalability](#scalability)
- [Monitoring & Observability](#monitoring--observability)

---

## Architecture Principles

### Clean Architecture

The application follows Uncle Bob's Clean Architecture with clear boundaries between layers:

```
┌────────────────────────────────────┐
│     External Interfaces (API)     │
├────────────────────────────────────┤
│         Interface Adapters         │
│    (Routes, Controllers, DTOs)     │
├────────────────────────────────────┤
│        Business Logic (Services)   │
├────────────────────────────────────┤
│     Data Access (Repositories)     │
├────────────────────────────────────┤
│      Entities (Models, Database)   │
└────────────────────────────────────┘
```

### Core Principles

1. **Dependency Rule**: Dependencies point inward
   - Outer layers depend on inner layers
   - Inner layers know nothing about outer layers

2. **Independence**
   - Framework independence
   - Database independence
   - UI independence
   - Testability

3. **Single Responsibility Principle**
   - Each module has one reason to change
   - Clear separation of concerns

4. **Open/Closed Principle**
   - Open for extension
   - Closed for modification

---

## Layer Architecture

### 1. API Layer (`app/api/`)

**Purpose**: Handle HTTP requests and responses

**Responsibilities**:
- Route definitions
- Request validation
- Response formatting
- HTTP status codes
- Exception handling

**Example**:
```python
# app/api/routes/user_routes.py

from fastapi import APIRouter, Depends, HTTPException, status
from app.services.user_service import UserService
from app.schemas.user_dto import UserResponse, UserCreateDTO

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateDTO,
    service: UserService = Depends(get_user_service)
):
    """
    Create a new user.
    
    - **name**: User's full name
    - **email**: User's email address
    - **password**: User's password (will be hashed)
    """
    try:
        user = service.create_user(user_data)
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
```

**Key Points**:
- Minimal business logic
- Delegates to service layer
- Returns Pydantic models
- Handles HTTP-specific concerns

### 2. Schema Layer (`app/schemas/`)

**Purpose**: Data validation and serialization

**Responsibilities**:
- Input validation
- Output serialization
- Type safety
- Data transfer objects (DTOs)

**Example**:
```python
# app/schemas/user_dto.py

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserCreateDTO(BaseModel):
    """Data required to create a user"""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserUpdateDTO(BaseModel):
    """Data that can be updated for a user"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)

class UserResponse(BaseModel):
    """User data returned by API"""
    id: int
    name: str
    email: EmailStr
    role: str
    created_at:  datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}
```

**Key Points**:
- Pydantic validation
- Separate DTOs for input/output
- No database dependencies
- Clear field constraints

### 3. Service Layer (`app/services/`)

**Purpose**: Business logic and orchestration

**Responsibilities**: 
- Business rules
- Transaction management
- Cross-cutting concerns
- Orchestrate multiple repositories

**Example**:
```python
# app/services/user_service.py

from typing import List, Optional
from sqlalchemy.orm import Session
from app. repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.schemas.user_dto import UserCreateDTO, UserUpdateDTO
from app.db.models.user import User
from app.core.security import verify_password

class UserService:
    """User business logic"""
    
    def __init__(self, db_session: Session):
        self.user_repo = UserRepository(db_session)
        self.token_repo = RefreshTokenRepository(db_session)
    
    def create_user(self, user_data: UserCreateDTO) -> User:
        """
        Create a new user with business logic validation.
        
        Business Rules:
        - Email must be unique
        - Password must be hashed
        - Default role is 'user'
        """
        # Check business rule
        existing_user = self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Delegate to repository
        return self.user_repo.create(user_data)
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user credentials.
        
        Business Rules:
        - User must exist
        - Password must match
        - Account must not be locked
        """
        user = self.user_repo.get_by_email(email)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        # Additional business logic (e.g., check if account is locked)
        return user
```

**Key Points**:
- Contains business logic
- Coordinates multiple repositories
- Throws domain exceptions
- Transaction boundaries

### 4. Repository Layer (`app/repositories/`)

**Purpose**: Data access abstraction

**Responsibilities**: 
- CRUD operations
- Query building
- Database interaction
- Data mapping

**Example**:
```python
# app/repositories/user_repository.py

from typing import List, Optional
from sqlalchemy.orm import Session
from app.db. models.user import User
from app.schemas.user_dto import UserCreateDTO, UserUpdateDTO
from app.core.security import hash_password

class UserRepository:
    """User data access layer"""
    
    def __init__(self, db:  Session):
        self.db = db
    
    def create(self, user_data: UserCreateDTO) -> User:
        """Insert new user into database"""
        user = User(
            name=user_data.name,
            email=user_data.email,
            hashed_password=hash_password(user_data.password)
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self. db.query(User).filter(User.email == email).first()
    
    def list(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List users with pagination"""
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def update(self, user_id: int, user_data: UserUpdateDTO) -> Optional[User]:
        """Update existing user"""
        user = self. get_by_id(user_id)
        if not user: 
            return None
        
        update_data = user_data.model_dump(exclude_unset=True)
        if "password" in update_data: 
            update_data["hashed_password"] = hash_password(update_data. pop("password"))
        
        for key, value in update_data. items():
            setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def delete(self, user_id:  int) -> bool:
        """Delete user by ID"""
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        self.db.delete(user)
        self.db.commit()
        return True
```

**Key Points**:
- No business logic
- Pure data access
- Reusable queries
- Database-specific operations

### 5. Model Layer (`app/db/models/`)

**Purpose**: Database schema definition

**Responsibilities**:
- Table structure
- Relationships
- Constraints
- Database mapping

**Example**:
```python
# app/db/models/user.py

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.db. models.base import Base

class User(Base):
    """User database model"""
    
    __tablename__ = "users"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Fields
    name = Column(String(100), nullable=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    role = Column(String(50), default="user")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc)
    )
    
    # Relationships
    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
```

**Key Points**:
- SQLAlchemy models
- Database constraints
- Relationships defined
- No business logic

---

## Data Flow

### Request/Response Flow

```
HTTP Request
    ↓
API Layer (Router)
    ↓
Schema Validation (Pydantic)
    ↓
Service Layer (Business Logic)
    ↓
Repository Layer (Data Access)
    ↓
Database (PostgreSQL/SQLite)
    ↓
Repository Layer (Data Mapping)
    ↓
Service Layer (Post-processing)
    ↓
Schema Serialization (Pydantic)
    ↓
API Layer (Response)
    ↓
HTTP Response
```

### Example: User Registration Flow

```python
# 1. HTTP Request
POST /auth/register
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securepass123"
}

# 2. Router receives and validates
@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreateDTO, db: Session = Depends(get_db)):
    # Pydantic validates input automatically
    
    # 3. Call service
    user_service = UserService(db)
    user = user_service.create_user(user_data)
    
    # 4. Return validated response
    return UserResponse.model_validate(user)

# 5. Service applies business logic
class UserService: 
    def create_user(self, user_data: UserCreateDTO) -> User:
        # Check if user exists
        existing = self. user_repo.get_by_email(user_data.email)
        if existing:
            raise ValueError("Email already exists")
        
        # 6. Repository saves to database
        return self.user_repo.create(user_data)

# 7. Repository interacts with database
class UserRepository: 
    def create(self, user_data: UserCreateDTO) -> User:
        user = User(
            name=user_data.name,
            email=user_data.email,
            hashed_password=hash_password(user_data.password)
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

# 8. HTTP Response
{
  "id":  1,
  "name":  "John Doe",
  "email": "john@example.com",
  "role": "user",
  "created_at":  "2026-01-22T10:30:00Z",
  "updated_at": "2026-01-22T10:30:00Z"
}
```

---

## Design Patterns

### 1. Repository Pattern

**Purpose**: Abstract data access logic

**Benefits**:
- Loose coupling
- Testability
- Swappable data sources
- Centralized queries

**Implementation**:
```python
# Abstract interface (optional)
from abc import ABC, abstractmethod

class IUserRepository(ABC):
    @abstractmethod
    def create(self, user_data: UserCreateDTO) -> User:
        pass
    
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        pass

# Concrete implementation
class UserRepository(IUserRepository):
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, user_data: UserCreateDTO) -> User:
        # Implementation
        pass
```

### 2. Dependency Injection

**Purpose**: Provide dependencies from outside

**Benefits**:
- Testability
- Flexibility
- Loose coupling

**Implementation**:
```python
# Dependency provider
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db. close()

def get_user_service(db:  Session = Depends(get_db)) -> UserService:
    return UserService(db)

# Usage in route
@router.get("/users")
async def list_users(service: UserService = Depends(get_user_service)):
    return service.list_users()
```

### 3. DTO (Data Transfer Object) Pattern

**Purpose**: Transfer data between layers

**Benefits**: 
- Type safety
- Validation
- Decoupling
- Clear contracts

**Implementation**:
```python
# Input DTO
class UserCreateDTO(BaseModel):
    name: str
    email: EmailStr
    password: str

# Output DTO
class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime
    
    model_config = {"from_attributes": True}
```

### 4. Factory Pattern

**Purpose**: Create objects without specifying exact class

**Implementation**:
```python
class ServiceFactory:
    @staticmethod
    def create_user_service(db: Session) -> UserService:
        return UserService(db)
    
    @staticmethod
    def create_auth_service(db: Session) -> AuthService:
        return AuthService(db)
```

### 5. Strategy Pattern

**Purpose**: Define family of algorithms

**Example**:
```python
from abc import ABC, abstractmethod

class AuthenticationStrategy(ABC):
    @abstractmethod
    def authenticate(self, credentials: dict) -> Optional[User]:
        pass

class EmailPasswordAuth(AuthenticationStrategy):
    def authenticate(self, credentials: dict) -> Optional[User]:
        # Email/password authentication
        pass

class OAuth2Auth(AuthenticationStrategy):
    def authenticate(self, credentials:  dict) -> Optional[User]:
        # OAuth2 authentication
        pass

class AuthService:
    def __init__(self, strategy: AuthenticationStrategy):
        self.strategy = strategy
    
    def login(self, credentials: dict) -> Optional[User]:
        return self.strategy.authenticate(credentials)
```

---

## Security Architecture

### Authentication Flow

```
┌──────┐                ┌──────────┐                ┌──────────┐
│Client│                │   API    │                │   DB     │
└──┬───┘                └────┬─────┘                └────┬─────┘
   │                         │                           │
   │  POST /auth/register    │                           │
   ├────────────────────────>│                           │
   │  {email, password}      │    Save user              │
   │                         ├──────────────────────────>│
   │                         │                           │
   │                         │<──────────────────────────┤
   │  201 Created            │    User created           │
   │<────────────────────────┤                           │
   │                         │                           │
   │  POST /auth/token       │                           │
   ├────────────────────────>│                           │
   │  {email, password}      │    Verify credentials     │
   │                         ├──────────────────────────>│
   │                         │                           │
   │                         │<──────────────────────────┤
   │                         │    User found             │
   │                         │                           │
   │                         │  Create JWT + Refresh     │
   │                         │◄──────────┐               │
   │                         │           │               │
   │                         │           │               │
   │  {access_token, ... }    │  Save refresh token       │
   │<────────────────────────┤──────────────────────────>│
   │                         │                           │
   │  GET /auth/me           │                           │
   │  Authorization: Bearer  │                           │
   ├────────────────────────>│                           │
   │                         │  Validate JWT             │
   │                         │◄──────────┐               │
   │                         │           │               │
   │                         │  Get user data            │
   │                         ├──────────────────────────>│
   │                         │                           │
   │                         │<──────────────────────────┤
   │  {user_data}            │                           │
   │<────────────────────────┤                           │
   │                         │                           │
```

### JWT Token Structure

```
Header. Payload.Signature

Header:
{
  "alg": "HS256",
  "typ": "JWT"
}

Payload: 
{
  "sub": "user@example.com",
  "role": "user",
  "exp": 1706789000
}

Signature:
HMACSHA256(
  base64UrlEncode(header) + "." +
  base64UrlEncode(payload),
  secret_key
)
```

### Security Measures

1. **Password Security**
   - Bcrypt hashing (cost factor: 12)
   - Salt automatically generated
   - Never store plain passwords

2. **JWT Security**
   - Short expiration (60 minutes)
   - Signed with secret key
   - Validated on every request

3. **Refresh Tokens**
   - Long expiration (7 days)
   - Stored in database
   - Can be revoked
   - One-time use

4. **CORS Protection**
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://trusted-domain.com"],
       allow_credentials=True,
       allow_methods=["GET", "POST", "PUT", "DELETE"],
       allow_headers=["Authorization", "Content-Type"],
   )
   ```

5. **Input Validation**
   - Pydantic validates all inputs
   - Type checking
   - Length constraints
   - Format validation

6. **SQL Injection Prevention**
   - SQLAlchemy ORM (parameterized queries)
   - No string concatenation
   - Automatic escaping

---

## Database Design

### Entity-Relationship Diagram

```
┌─────────────────┐
│      User       │
├─────────────────┤
│ id (PK)         │
│ name            │
│ email (UNIQUE)  │
│ hashed_password │
│ role            │
│ created_at      │
│ updated_at      │
└────────┬────────┘
         │ 1
         │
         │ N
         │
┌────────┴────────────┐
│   RefreshToken      │
├─────────────────────┤
│ id (PK)             │
│ token (UNIQUE)      │
│ user_id (FK)        │
│ expires_at          │
│ revoked             │
│ created_at          │
│ updated_at          │
└─────────────────────┘
```

### Database Indexes

```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
```

### Migration Strategy

1. **Development**
   ```bash
   # Create migration
   alembic revision --autogenerate -m "add column"
   
   # Apply migration
   alembic upgrade head
   ```

2. **Staging**
   ```bash
   # Test migration
   alembic upgrade head
   
   # Verify data integrity
   # Run tests
   
   # Rollback if needed
   alembic downgrade -1
   ```

3. **Production**
   ```bash
   # Backup database
   pg_dump database > backup.sql
   
   # Apply migration
   alembic upgrade head
   
   # Monitor for issues
   # Rollback if critical issues
   ```

---

## Testing Strategy

### Test Pyramid

```
       /\
      /  \      ← E2E Tests (Few, Slow)
     /────\
    /      \    ← Integration Tests (Some, Medium)
   /────────\
  /          \  ← Unit Tests (Many, Fast)
 /────────────\
```

### 1. Unit Tests

**Target**: Individual functions/methods

**Example**:
```python
def test_hash_password():
    """Test password hashing"""
    password = "mypassword"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)
```

### 2. Integration Tests

**Target**:  Multiple components working together

**Example**: 
```python
def test_user_repository_create(db_session):
    """Test repository creates user in database"""
    repo = UserRepository(db_session)
    user_data = UserCreateDTO(
        name="Test User",
        email="test@example.com",
        password="password123"
    )
    
    user = repo.create(user_data)
    
    assert user.id is not None
    assert user.email == user_data.email
    
    # Verify in database
    db_user = db_session.query(User).filter(User.id == user.id).first()
    assert db_user is not None
```

### 3. API Tests (E2E)

**Target**: Full request/response cycle

**Example**: 
```python
def test_register_and_login_flow(client):
    """Test complete registration and login flow"""
    # Register
    register_response = client.post(
        "/auth/register",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "password": "securepass123"
        }
    )
    assert register_response.status_code == 201
    
    # Login
    login_response = client. post(
        "/auth/token",
        data={
            "username": "john@example.com",
            "password": "securepass123"
        }
    )
    assert login_response. status_code == 200
    assert "access_token" in login_response.json()
    
    # Access protected endpoint
    token = login_response.json()["access_token"]
    me_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "john@example.com"
```

### Coverage Goals

- **Unit Tests**: >80%
- **Integration Tests**: >60%
- **E2E Tests**: Critical user paths

---

## Scalability

### Horizontal Scaling

**Stateless Design**:
- No session state in application
- JWT for authentication (no server-side sessions)
- Database for persistent state

**Load Balancing**:
```
         ┌──────────────┐
         │ Load Balancer│
         └───────┬──────┘
                 │
       ┌─────────┴─────────┐
       │                   │
   ┌───▼───┐           ┌───▼───┐
   │ API 1 │           │ API 2 │
   └───┬───┘           └───┬───┘
       │                   │
       └─────────┬─────────┘
                 │
           ┌─────▼─────┐
           │  Database │
           └───────────┘
```

### Caching Strategy

**Application-Level Caching**:
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_settings() -> Settings:
    return Settings()
```

**Redis Caching** (Future):
```python
import redis
from fastapi import Depends

redis_client = redis.Redis(host='localhost', port=6379)

@app.get("/users/{user_id}")
async def get_user(user_id:  int):
    # Try cache first
    cached = redis_client.get(f"user:{user_id}")
    if cached:
        return json. loads(cached)
    
    # Get from database
    user = db.query(User).filter(User.id == user_id).first()
    
    # Cache for 5 minutes
    redis_client.setex(
        f"user:{user_id}",
        300,
        json.dumps(user)
    )
    
    return user
```

### Database Optimization

**Connection Pooling**:
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
```

**Query Optimization**:
```python
# Avoid N+1 queries
users = db.query(User).options(
    joinedload(User.refresh_tokens)
).all()

# Use pagination
users = db. query(User).offset(skip).limit(limit).all()

# Use select specific columns
users = db.query(User. id, User.email).all()
```

---

## Monitoring & Observability

### Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@app.get("/users")
async def list_users():
    logger.info("Fetching users list")
    users = user_service.list_users()
    logger.info(f"Returned {len(users)} users")
    return users
```

### Metrics (Future:  Prometheus)

```python
from prometheus_client import Counter, Histogram

request_count = Counter('requests_total', 'Total requests')
request_duration = Histogram('request_duration_seconds', 'Request duration')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    request_count.inc()
    
    with request_duration.time():
        response = await call_next(request)
    
    return response
```

### Health Checks

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
```

---

## Future Enhancements

- [ ] Add Redis for caching
- [ ] Implement rate limiting
- [ ] Add WebSocket support
- [ ] Integrate Celery for background tasks
- [ ] Add OpenTelemetry for distributed tracing
- [ ] Implement API versioning
- [ ] Add GraphQL support
- [ ] Implement event sourcing
- [ ] Add CQRS pattern

---

**For detailed usage instructions, see [USAGE_GUIDE.md](./USAGE_GUIDE.md)**

**Made with ❤️ by [Alwil17](https://github.com/Alwil17)**
