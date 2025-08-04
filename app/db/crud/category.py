from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.db.models.category import Category
from app.db.schemas import category as schema


async def get_all(session: AsyncSession) -> list[Category]:
    result = await session.execute(
        select(Category)
    )
    return result.scalars().all()


async def create(session: AsyncSession, data: schema.CategoryCreate) -> schema.CategoryRead:
    obj = Category(**data.dict())
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    result = await session.execute(
        select(Category).options(selectinload(Category.items)).where(Category.id == obj.id)
    )
    obj_with_items = result.scalar_one()
    return schema.CategoryRead.from_orm(obj_with_items)
