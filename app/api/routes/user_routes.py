from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.roles import Role
from app.core.security import require_role
from app.db.base import get_db
from app.schemas.user_dto import UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])

MAX_PAGE_SIZE = 100


@router.get(
    "",
    response_model=list[UserResponse],
    dependencies=[Depends(require_role(Role.ADMIN))],
)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
):
    """List users (admin only), ordered by id."""
    return UserService(db).list_users(skip=skip, limit=limit)
