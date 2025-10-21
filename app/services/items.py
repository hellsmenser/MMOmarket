from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import item as crud
from app.db.schemas.category import CategoryShort
from app.db.schemas.item import ItemCreate, ItemUpdate, ItemOut, ItemActivity, ItemSearchOut
from app.core.redis import redis_cache


async def create_item(db: AsyncSession, item_in: ItemCreate) -> ItemOut:
    return await crud.create_item(db, item_in)


async def get_items(db: AsyncSession, page: int, page_size: int) -> list[ItemOut]:
    items = await crud.get_items(db, page, page_size)
    return [ItemOut.model_validate(item) for item in items]


async def get_item(db: AsyncSession, item_id: int) -> ItemOut | None:
    return await crud.get_item(db, item_id)


async def update_item(db: AsyncSession, item_id: int, item_in: ItemUpdate) -> ItemOut | None:
    return await crud.update_item(db, item_id, item_in)


async def delete_item(db: AsyncSession, item_id: int) -> bool:
    return await crud.delete_item(db, item_id)


@redis_cache(ttl=7200, model=ItemActivity, is_list=True)
async def get_top_active_items(db: AsyncSession, category_id: int | None = None) -> list[ItemActivity]:
    volatility = await crud.get_top_active_items(db, category_id=category_id)
    return [
        ItemActivity(
            id=row[0],
            name=row[1],
            category=CategoryShort(id=row[2], name=row[3]),
            currency=row[4],
            activity=row[5],
            price=int(round(row[6])) if row[6] is not None else None
        )
        for row in volatility
    ]


async def search_items(db: AsyncSession, query: str, page: int = 1, page_size: int = 20) -> ItemSearchOut:
    items = await crud.search_items_by_name(db, query, page, page_size)
    return items
