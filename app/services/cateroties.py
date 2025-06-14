from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import category as crud
from app.db.schemas.category import CategoryCreate


async def get_all(session: AsyncSession):
    return await crud.get_all(session)

async def create(session: AsyncSession, data: CategoryCreate):
    return await crud.create(session, data)