from pydantic import BaseModel
from fastapi_users import schemas

from auth.models import RoleType

# class UserRead(schemas.BaseUser[int]):
#     pass
# class UserUpdate(schemas.BaseUserUpdate):
#     pass


class UserCreate(schemas.BaseUserCreate):
    user_id: int


class RegData(BaseModel):
    
    email: str
    password: str
    username: str
    first_name: str
    last_name: str
    role: RoleType
