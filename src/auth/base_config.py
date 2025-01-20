from fastapi.security import OAuth2AuthorizationCodeBearer
from fastapi_users.authentication import (
                                            AuthenticationBackend,
                                            JWTStrategy,
                                            CookieTransport,
                                            BearerTransport
                                        )
from fastapi_users import FastAPIUsers

from config import setting
from auth.models import LocalAccount
from auth.manager import get_user_manager


#   token's ttls
LIFETIME_ACCESS=60 * 3
LIFETIME_REFRESH=60 * 60 * 24

#   token's transports
cookie_transport = CookieTransport(
    cookie_name=f'refresh_token',
    cookie_max_age=LIFETIME_REFRESH
)

bearer_transport = BearerTransport(
    tokenUrl=f"auth/jwt/login"
)

#   access token's strategy
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=setting.SECRET_AUTH,
        lifetime_seconds=LIFETIME_ACCESS
    )

#   refresh token's strategy
def get_refresh_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=setting.SECRET_AUTH,
        lifetime_seconds=LIFETIME_REFRESH
    )

#   token's backend
auth_access_backend = AuthenticationBackend(
    name=f'access_jwt',
    transport=bearer_transport,
    get_strategy=get_jwt_strategy
)

auth_refresh_backend = AuthenticationBackend(
    name=f'refresh_jwt',
    transport=cookie_transport,
    get_strategy=get_refresh_jwt_strategy
)

fastapi_users = FastAPIUsers[LocalAccount, int](
    get_user_manager=get_user_manager,
    auth_backends=[auth_access_backend, auth_refresh_backend]
)

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=setting.GITHUB_AUTH_URL,
    tokenUrl=setting.GITHUB_TOKEN_URL
)