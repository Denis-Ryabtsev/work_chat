from typing import AsyncGenerator, Union

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import (
                                    async_sessionmaker, 
                                    create_async_engine,
                                    AsyncSession
                                )
from redis.asyncio import Redis

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


async def get_redis_client() -> Union[Redis, Exception]:
    client = Redis(
        host=setting.REDIS_HOST, 
        port=setting.REDIS_PORT, 
        decode_responses=True
    )
    try:
        await client.ping()
        return client
    except Exception as error:
        raise RuntimeError(
            f"Failed to connect to Redis: {str(error)}"
        )

async def check_token_blacklist(token: str, redis: Redis) -> bool:
    return await redis.exists(f"blacklist:{token}") > 0

