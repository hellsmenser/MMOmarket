from sqlalchemy.ext.asyncio import AsyncSession

from app.db.schemas.auth import UserRegister, UserResponse
from app.db.crud.user import create_user as crud_create_user
from app.db.crud.user import authenticate_user as crud_authenticate_user


async def create_user(db: AsyncSession, user: UserRegister) -> UserResponse:
    db_user = await crud_create_user(db, user)
    return UserResponse(id=db_user.id, username=db_user.username)


async def authenticate_user(db: AsyncSession, username: str, password: str) -> UserResponse | None:
    db_user = await crud_authenticate_user(db, username, password)
    return UserResponse(id=db_user.id, username=db_user.username) if db_user else None


async def get_me(db: AsyncSession, user_id: int) -> UserResponse | None:
    from app.db.crud.user import get_user_by_id
    db_user = await get_user_by_id(db, user_id)
    return UserResponse(id=db_user.id, username=db_user.username) if db_user else None