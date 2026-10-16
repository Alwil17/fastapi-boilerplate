from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.rate_limit import rate_limit
from app.core.security import create_access_token, get_current_user
from app.db.base import get_db
from app.schemas.auth_dto import RefreshTokenRequest, TokenResponse
from app.schemas.user_dto import UserCreateDTO, UserResponse
from app.services.token_service import InvalidRefreshToken, TokenService
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(settings.RATE_LIMIT_REGISTER, "register"))],
)
def register(user_data: UserCreateDTO, db: Session = Depends(get_db)):
    """Register a new user."""
    user_service = UserService(db)
    try:
        user = user_service.create_user(user_data)
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post(
    "/token",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit(settings.RATE_LIMIT_LOGIN, "login"))],
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
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

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=TokenService(db).issue(user.id),
        token_type="bearer",  # nosec B106
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@router.post(
    "/refresh",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit(settings.RATE_LIMIT_REFRESH, "refresh"))],
)
def refresh_access_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Exchange a refresh token for a new access/refresh pair (single-use rotation)."""
    try:
        user, new_refresh_token = TokenService(db).rotate(request.refresh_token)
    except InvalidRefreshToken as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=new_refresh_token,
        token_type="bearer",  # nosec B106
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Revoke a refresh token (and every token rotated from it)."""
    TokenService(db).revoke(request.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke every refresh token of the current user (all devices)."""
    TokenService(db).revoke_all(current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
