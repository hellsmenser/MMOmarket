import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import logging

from app.config import get_database_url

DATABASE_URL = get_database_url()
logging.info("PostgreSQL backend")

engine = create_async_engine(
    DATABASE_URL,
    echo=bool(int(os.getenv("SQLALCHEMY_ECHO", "0"))),
    pool_pre_ping=True,
    pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    logging.info("Init skipped (use Alembic)")
