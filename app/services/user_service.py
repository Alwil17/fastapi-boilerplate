from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.security import verify_password
from app.db.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user_dto import UserCreateDTO, UserResponse, UserUpdateDTO

USER_NOT_FOUND = "User not found"

class UserService:
    def __init__(self, db_session: Session):
        self.repository = UserRepository(db_session)

    def create_user(self, user_data: UserCreateDTO) -> User:
        existing_user = self.repository.get_by_email(user_data.email)
        if existing_user:
            raise ValueError("An user with this email already exists.")
        return self.repository.create(user_data)

    def get_user_by_email(self, email: str) -> User:
        return self.repository.get_by_email(email)

    def authenticate_user(self, email: str, password: str) -> User:
        user = self.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.repository.get_by_id(user_id)

    def list_users(self) -> List[User]:
        return self.repository.list()

    def update_user(self, user_id: int, user_data: UserUpdateDTO) -> Optional[User]:
        return self.repository.update(user_id, user_data)

    def delete_user(self, user_id: int) -> bool:
        return self.repository.delete(user_id)
