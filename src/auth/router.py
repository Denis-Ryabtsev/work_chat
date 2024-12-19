from typing import Optional, Union

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from auth.schemas import UserCreate, RegData
from auth.manager import UserManager
from auth.models import User
from auth.base_config import fastapi_users
from database import get_session

reg_router = APIRouter(
    prefix=f"/local_acc",
    tags=[f'Registration']
)

@reg_router.post(f"/registration", response_model=Optional[str])
async def local_account_registration(
    data: RegData,
    user_manager: UserManager = Depends(fastapi_users.get_user_manager),
    session: AsyncSession = Depends(get_session)
) -> Union[str, HTTPException]:
    
    try:
        user_info = User(
            username=data.username,
            first_name=data.first_name,
            last_name=data.last_name,
            role=data.role
        )
        session.add(user_info)
        await session.flush()

        user_account = UserCreate(
            email=data.email,
            password=data.password,
            user_id=user_info.id,
            is_active=True,
            is_superuser=False,
            is_verified=False
        )
        
        await user_manager.create(user_account)
        await session.commit()
        
        return f"Registration was successful"
    except Exception as error:
        raise HTTPException(
            status_code=499,
            detail=str(error)
        )