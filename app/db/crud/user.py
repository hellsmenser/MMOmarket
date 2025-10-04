from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.utils.security import hash_password, verify_password
from app.db.schemas.auth import UserRegister


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_data: UserRegister) -> User:
    existing = await get_user_by_username(db, user_data.username)
    if existing:
        raise ValueError("Username already exists")
    hashed_password = hash_password(user_data.password)
    db_user = User(
        username=user_data.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    user = await get_user_by_username(db, username)  # добавлен await
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user
