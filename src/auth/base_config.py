from fastapi_users.authentication import (AuthenticationBackend,\
                                          JWTStrategy,\
                                          CookieTransport,
                                          BearerTransport    
                                        )

from fastapi_users import FastAPIUsers

from config import setting
from auth.models import LocalAccount
from auth.manager import get_user_manager

LIFETIME_ACCESS=60 * 10
LIFETIME_REFRESH=60 * 60 * 24

cookie_transport = CookieTransport(
    cookie_name=f'refresh_token',
    cookie_max_age=LIFETIME_REFRESH
)

bearer_transport = BearerTransport(
    tokenUrl=f"auth/jwt/login"
)

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=setting.SECRET_AUTH,
        lifetime_seconds=LIFETIME_ACCESS
    )

def get_refresh_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=setting.SECRET_AUTH,
        lifetime_seconds=LIFETIME_REFRESH
    )

auth_backend = AuthenticationBackend(
    name=f'jwt',
    transport=bearer_transport,
    get_strategy=get_jwt_strategy
)

fastapi_users = FastAPIUsers[LocalAccount, int](
    get_user_manager=get_user_manager,
    auth_backends=[auth_backend]
)