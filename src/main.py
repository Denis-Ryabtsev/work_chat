from fastapi import FastAPI

from auth.router import reg_router, auth_router, test_router, logout_router

app = FastAPI(
    title=f"Work_Chat"
)

app.include_router(reg_router)
app.include_router(auth_router)
app.include_router(test_router)
app.include_router(logout_router)