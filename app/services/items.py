from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import item as crud
from app.db.schemas.item import ItemCreate, ItemUpdate

async def create_item(db: AsyncSession, item_in: ItemCreate):
    return await crud.create_item(db, item_in)

async def get_items(db: AsyncSession):
    return await crud.get_items(db)

async def get_item(db: AsyncSession, item_id: int):
    return await crud.get_item(db, item_id)

async def update_item(db: AsyncSession, item_id: int, item_in: ItemUpdate):
    return await crud.update_item(db, item_id, item_in)

async def delete_item(db: AsyncSession, item_id: int):
    return await crud.delete_item(db, item_id)