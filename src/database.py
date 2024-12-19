from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import (
                                    async_sessionmaker, 
                                    create_async_engine,
                                    AsyncSession
                                )

from config import setting


engine = create_async_engine(
    url=setting.DB_URL,
    echo=True,
    pool_size=5,
    max_overflow=3
)

a_session = async_sessionmaker(engine)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with a_session() as session:
        yield session

class Base(DeclarativeBase):
    pass