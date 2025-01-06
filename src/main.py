import os
from fastapi import APIRouter, FastAPI, HTTPException, Request

from authlib.integrations.starlette_client import OAuth
from auth.router import reg_router, auth_router, test_router, logout_router
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
import binascii
from config import setting

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
# from models import User  # Ваша модель пользователя
from database import get_session  # Ваша зависимость для получения сессии
import os


from uuid import uuid4

app = FastAPI(
    title=f"Work_Chat"
)


app.include_router(reg_router)
app.include_router(auth_router)
app.include_router(test_router)
app.include_router(logout_router)
# app.include_router(oauth_router)

# Middleware для сессий
app.add_middleware(SessionMiddleware, secret_key=setting.SECRET_AUTH, max_age=3600, same_site="Lax")

# Настройка OAuth
oauth = OAuth()
github = oauth.register(
    name="github",
    client_id=setting.GITHUB_CLIENT_ID,
    client_secret=setting.GITHUB_CLIENT_SECRET,
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"},
)

# Эндпоинт для генерации ссылки
@app.get("/login")
async def login_via_github(request: Request):
    redirect_uri = "http://127.0.0.1:8000/auth/callback"  # URL редиректа
    # # Передаем объект `request` для корректной обработки
    # state = await github.create_authorization_url(redirect_uri)
    # print("\n\nState перед редиректом:", state)
    # print("\n\nСохраненное состояние в сессии: ", state['state'])
    # # Сохраняем state вручную
    # request.session["state"] = state["state"]
    # print("\n\nСессия перед редиректом:", request.session)
    # print("\n\nURL для авторизации:", state["url"])
    # return await github.authorize_redirect(request, redirect_uri)
    state = str(uuid4())
    request.session["state"] = state
    github_auth_url = f"https://github.com/login/oauth/authorize?response_type=code&client_id={setting.GITHUB_CLIENT_ID}&redirect_uri={redirect_uri}&state={state}"
    return RedirectResponse(github_auth_url)


# Эндпоинт для обработки редиректа от GitHub
@app.get("/auth/callback")
async def auth_callback(request: Request):
    try:
        state_in_request = request.query_params.get("state")
        state_in_session = request.session.get("state")

        print("\n\nState из запроса:", state_in_request)
        print("\n\nState из сессии:", state_in_session)
        print("\n\nQuery parameters на callback:", request.query_params)

        if state_in_request != state_in_session:
            raise HTTPException(
                status_code=401,
                detail="CSRF Warning! State mismatch between request and session.",
            ) 
        # Получаем токен доступа
        token = await github.authorize_access_token(request)
        # Используем токен для запроса данных пользователя
        user = await github.get("user", token=token)
        user_data = user.json()
        return {"user": user_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка авторизации: {e}")




@app.middleware("http")
async def debug_session(request: Request, call_next):
    print("\n\nКуки запроса:", request.cookies)
    response = await call_next(request)
    print("\n\nКуки ответа:", response.headers.get("set-cookie"))
    return response


# http://127.0.0.1:8000/login