from datetime import datetime
from typing import Optional, Union

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi_users.exceptions import UserAlreadyExists, UserNotExists, InvalidVerifyToken
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from auth.schemas import UserCreate, RegData, LoginData
from auth.manager import UserManager, get_user_manager
from auth.models import User, LocalAccount
from auth.base_config import (
                                fastapi_users,
                                auth_refresh_backend,
                                auth_access_backend,
                                cookie_transport
                            )
from database import get_session, get_redis_client, check_token_blacklist
from config import setting


reg_router = APIRouter(
    prefix=f"/registration",
    tags=[f'Registration']
)

auth_router = APIRouter(
    prefix=f"/auth",
    tags=[f'Authentification']
)

logout_router = APIRouter(
    tags=[f"Authentification"]
)

test_router = APIRouter(
    tags=[f"Test"]
)


@reg_router.post(f"/local_acc", response_model=Optional[str])
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


@auth_router.post(f'/login', response_model=Optional[dict])
async def login_user(
    response: Response,
    data: LoginData,
    user_manager = Depends(get_user_manager) 
) -> Union[dict, HTTPException]:
    
    try:
        user = await user_manager.get_by_email(data.email)
        verify_pass, _ = user_manager.password_helper.verify_and_update(
            data.password, 
            user.hashed_password
        )
        if not verify_pass: 
            raise
    except UserNotExists:
        raise HTTPException(
            status_code=404,
            detail=f"This email not found"
        )
    except:
        raise HTTPException(
            status_code=474,
            detail=f"Email or password is invalid"
        )

    access_token = await auth_access_backend.get_strategy().write_token(user)
    refresh_token = await auth_refresh_backend.get_strategy().write_token(user)

    response.set_cookie(
        key=cookie_transport.cookie_name,
        value=refresh_token,
        max_age=cookie_transport.cookie_max_age
    )

    return {f'access_token': access_token, f'token_type': f'Bearer'}


@test_router.get(f"/check_access_token", response_model=dict)
async def check_access_token(
    user: LocalAccount = Depends(fastapi_users.current_user())
) -> dict:
    """
    Проверяет валидность access токена.
    Если токен валиден, возвращает данные пользователя.
    Если токен истёк или недействителен, возвращает ошибку 401.
    """
    return {
        "message": "Access token is valid",
        "user_id": user.id,
        "email": user.email,
    }
    # return await f"{check_token_blacklist(f"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiYXVkIjpbImZhc3RhcGktdXNlcnM6YXV0aCJdLCJleHAiOjE3MzQ5MjQxODN9.w5X1mnVdlxWaADLgecLH2_kfSiynC-vOeWt7rr7dy0E")}"

@test_router.get(f"/check", response_model=bool)
async def check(
    request: Request,
    redis: Redis = Depends(get_redis_client)
) -> bool:
    """
    Проверяет валидность access токена.
    Если токен валиден, возвращает данные пользователя.
    Если токен истёк или недействителен, возвращает ошибку 401.
    """
    headers = request.headers.get(f"Authorization")
    token = headers.split(" ")[1]
    return await check_token_blacklist(token, redis)

@auth_router.post(f"/refresh_token", response_model=Optional[dict])
async def refresh_access_token(
    request: Request,
    user_manager: UserManager = Depends(fastapi_users.get_user_manager)
) -> Union[dict, HTTPException]:

    refresh_token = request.cookies.get(cookie_transport.cookie_name)
    if not refresh_token:
        raise HTTPException(
            status_code=491,
            detail=f"Refresh token is apsent"
        )
    
    try:
        refresh_user = await auth_refresh_backend.get_strategy().read_token(refresh_token, user_manager)
        if not refresh_user:
            raise InvalidVerifyToken()
        
        access_token = await auth_access_backend.get_strategy().write_token(refresh_user)
        return {f"access_token": access_token, f"token_type": f"Bearer"}
    except InvalidVerifyToken:
        raise HTTPException(
            status_code=492,
            detail=f"Refresh token is inactive"
        )
    
@logout_router.post(f"/logout", response_model=Optional[str])
async def logout_user(
    response: Response,
    request: Request,
    redis_client: Redis = Depends(get_redis_client)
) -> Union[str, HTTPException]:
    
    try:
        headers = request.headers.get(f"Authorization")
        if headers and headers.startswith(f"Bearer "):
            token = headers.split(" ")[1]
            payload = jwt.decode(token, key=setting.SECRET_AUTH, algorithms=[f'HS256'], audience=["fastapi-users:auth"])
            ttl = payload[f'exp'] - int(datetime.now().timestamp())
            if ttl > 0:
                await redis_client.setex(f"blacklist:{token}", ttl, f"true")           
        if request.cookies.get(cookie_transport.cookie_name):
            response.delete_cookie(cookie_transport.cookie_name)
        return f"Logout was successfull"
    except Exception as e:
        raise HTTPException(
            status_code=501,
            detail=str(e)
        )











