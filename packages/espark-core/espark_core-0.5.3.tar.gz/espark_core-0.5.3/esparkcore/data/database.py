from os import getenv

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from sqlmodel import SQLModel

from ..constants import ENV_DATABASE_URL

# pylint: disable=invalid-name
engine        = create_async_engine(getenv(ENV_DATABASE_URL, 'sqlite+aiosqlite:///database.db'), echo=True)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
