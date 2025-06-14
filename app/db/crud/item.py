from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from sqlalchemy.orm import selectinload

from app.db.models.item import Item
from app.db.schemas.item import ItemCreate, ItemUpdate


async def create_item(db: AsyncSession, item_in: ItemCreate) -> Item:
    db_item = Item(
        name=item_in.name,
        category_id=item_in.category_id,
        image=item_in.image,
        _modifications=",".join(str(m) for m in (item_in.modifications or []))
    )
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item


async def get_item(db: AsyncSession, item_id: int):
    result = await db.execute(
        select(Item)
        .options(
            selectinload(Item.category)
        )
        .where(Item.id == item_id)
    )
    return result.scalar_one_or_none()

async  def get_item_by_name(db: AsyncSession, item_name: str) -> Optional[Item]:
    stmt = select(Item).where(Item.name == item_name)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_items(db: AsyncSession):
    result = await db.execute(
        select(Item)
        .options(
            selectinload(Item.category)
        )
    )
    return result.scalars().all()

async def update_item(
    db: AsyncSession, item_id: int, item_in: ItemUpdate
) -> Optional[Item]:
    item = await get_item(db, item_id)
    if not item:
        return None

    if item_in.name is not None:
        item.name = item_in.name
    if item_in.image is not None:
        item.image = item_in.image
    if item_in.modifications is not None:
        item.modifications = ",".join(str(m) for m in item_in.modifications)
    if item_in.category_id is not None:
        item.category_id = item_in.category_id

    await db.commit()
    await db.refresh(item)
    return item


async def delete_item(
    db: AsyncSession, item_id: int
) -> bool:
    item = await get_item(db, item_id)
    if not item:
        return False
    await db.delete(item)
    await db.commit()
    return True
