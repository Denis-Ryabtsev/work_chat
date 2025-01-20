from fastapi import FastAPI

from auth.router import reg_router, auth_router, logout_router, oauth_router


app = FastAPI(
    title=f"Work_Chat",
    description="API for Work Chat application"
)


app.include_router(reg_router)
app.include_router(auth_router)
app.include_router(logout_router)
app.include_router(oauth_router)