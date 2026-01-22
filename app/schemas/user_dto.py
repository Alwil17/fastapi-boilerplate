from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreateDTO(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserUpdateDTO(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
