from fastapi import FastAPI

from auth.router import reg_router

app = FastAPI(
    title=f"Work_Chat"
)

app.include_router(reg_router)