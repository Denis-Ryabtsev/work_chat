from fastapi_users.authentication import (AuthenticationBackend,\
                                          JWTStrategy,\
                                          CookieTransport,
                                          BearerTransport
                                        )

from fastapi_users import FastAPIUsers
from httpx_oauth.clients.github import GitHubOAuth2

from config import setting
from auth.models import LocalAccount
from auth.manager import get_user_manager

LIFETIME_ACCESS=60 * 3
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

#   google cloud

# oauth_client = GoogleOAuth2(
#     client_id=setting.CLIENT_ID,
#     client_secret=setting.CLIENT_SECRET,
#     scopes=[
#         f"https://www.googleapis.com/auth/userinfo.profile", 
#         f"https://www.googleapis.com/auth/userinfo.email",
#         f"openid"
#     ]
#     # scopes=[
#     #     f"openid", 
#     #     f"email", 
#     #     f"profile"
#     # ]
# )

github_client = GitHubOAuth2(
    client_id=setting.GITHUB_CLIENT_ID,
    client_secret=setting.GITHUB_CLIENT_SECRET,
    scopes=[
        f"read:user",
        f"user:email"
    ]
)

