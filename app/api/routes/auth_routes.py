from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.schemas.user_dto import UserCreateDTO, UserResponse
from app.schemas.auth_dto import TokenResponse, RefreshTokenRequest
from app.services.user_service import UserService
from app.repositories.refresh_token_repository import RefreshTokenRepository
import secrets
from app.db.base import get_db
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

def create_refresh_token(user_id: int, db: Session):
    """Create a new refresh token for a user."""
    token = secrets.token_hex(32)
    expires_at = datetime.now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token_repo = RefreshTokenRepository(db)
    refresh_token_repo.create(user_id, token, expires_at)
    return token

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreateDTO, db: Session = Depends(get_db)):
    """Register a new user."""
    user_service = UserService(db)
    try:
        user = user_service.create_user(user_data)
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/token", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """Login and get access token."""
    user_service = UserService(db)
    user = user_service.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    refresh_token = create_refresh_token(user.id, db)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """Get current user information."""
    return current_user

@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    refresh_token_repo = RefreshTokenRepository(db)
    stored_token = refresh_token_repo.get_by_token(request.refresh_token)

    if not stored_token or stored_token.revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    if stored_token.expires_at < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired"
        )

    user_service = UserService(db)
    user = user_service.get_user_by_id(stored_token.user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    new_access_token = create_access_token(data={"sub": user.email, "role": user.role})
    new_refresh_token = create_refresh_token(user.id, db)

    # Revoke old refresh token
    refresh_token_repo.revoke(request.refresh_token)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer"
    )
