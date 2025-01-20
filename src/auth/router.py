from datetime import datetime
from typing import Optional, Union

from asyncpg.exceptions import UniqueViolationError
import httpx
import jwt
from fastapi import (
    APIRouter, 
    Depends, 
    HTTPException, 
    Request, 
    Response
)

from fastapi_users.exceptions import (
    UserNotExists, 
    UserAlreadyExists,
    InvalidVerifyToken, 
    InvalidPasswordException
)
from redis import Redis
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from auth.schemas import (
    UserCreate, 
    RegData, 
    LoginData, 
    UserGithub
)
from auth.manager import UserManager, get_user_manager
from auth.models import User, GithubAccount, LocalAccount
from auth.base_config import (
    fastapi_users,
    auth_refresh_backend,
    auth_access_backend,
    cookie_transport,
    oauth2_scheme
)
from database import get_session, get_redis_client
from config import setting


reg_router = APIRouter(
    prefix=f"/registration",
    tags=[f'Registration']
)

auth_router = APIRouter(
    prefix=f"/auth",
    tags=[f'Authentification']
)

oauth_router = APIRouter(
    prefix=f"/auth",
    tags=[f'Oauthentification']
)

logout_router = APIRouter(
    tags=[f"Authentification"]
)


@reg_router.post(f"/local_account", response_model=Optional[str])
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
    
    except UserAlreadyExists:
        raise HTTPException(
            status_code=499,
            detail=f"Input email is already exsists"
        )
    except IntegrityError:
        raise HTTPException(
            status_code=499,
            detail=f"Input username is already exists"
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
            raise InvalidPasswordException 
        
        access_token = await auth_access_backend.get_strategy().write_token(user)
        refresh_token = await auth_refresh_backend.get_strategy().write_token(user)

        response.set_cookie(
            key=cookie_transport.cookie_name,
            value=refresh_token,
            max_age=cookie_transport.cookie_max_age
        )

        return {f'access_token': access_token, f'token_type': f'Bearer'}
    
    except UserNotExists:
        raise HTTPException(
            status_code=404,
            detail=f"This email not found"
        )
    except InvalidPasswordException:
        raise HTTPException(
            status_code=474,
            detail=f"Email or password is invalid"
        )
    

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
            raise InvalidVerifyToken
        
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
            payload = jwt.decode(
                token, 
                key=setting.SECRET_AUTH, 
                algorithms=[f'HS256'], 
                audience=["fastapi-users:auth"]
            )
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


@oauth_router.get(f'/login', response_model=str)
async def login_github() -> str:
    return (
        f"{setting.GITHUB_AUTH_URL}?client_id={setting.GITHUB_CLIENT_ID}"\
        f"&redirect_uri={setting.GITHUB_REDIRECT_URI}&scope=read:user"
    )


@oauth_router.get(f"/callback", response_model=Optional[dict])
async def callback(
    code: str,
    current_user = Depends(fastapi_users.current_user()),
    session: AsyncSession = Depends(get_session)
) -> Union[HTTPException, dict]:
    
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            setting.GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": setting.GITHUB_CLIENT_ID,
                "client_secret": setting.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": setting.GITHUB_REDIRECT_URI,
            }
        )

        if token_response.status_code != 200:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to fetch access token"
            )

        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(
                status_code=400, 
                detail="No access token returned"
            )

        user_response = await client.get(
            setting.GITHUB_API_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if user_response.status_code != 200:
            raise HTTPException(
                status_code=400, 
                detail="Failed to fetch user info"
            )

        user_data = user_response.json()
        account = GithubAccount(
            login=user_data["login"],
            account_id=user_data['id'],
            name=user_data.get("name"),
            token=access_token,
            avatar_url=user_data.get("avatar_url")
        )
        session.add(account)
        session.flush()
        user = session.query(LocalAccount).filter(id=current_user.id).first()

        if user:
            user.oauth_id = account.id
            session.commit()


        return {"user": user, "access_token": access_token}


@oauth_router.get("/protected-route", response_model=dict)
async def protected_route(token: str = Depends(oauth2_scheme)) -> dict:
    return {"message": "You have access!", "token": token}

