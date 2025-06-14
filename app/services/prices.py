from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.crud import price as crud
from app.db.schemas.price import PriceCreate

async def add_prices_batch(db: AsyncSession, prices: List[PriceCreate]):
    return await crud.add_prices_batch(db, prices)

async def get_prices_by_item(
    db: AsyncSession,
    item_id: int,
    limit: int = 100,
    enchant_level: Optional[int] = None,
    currency: Optional[str] = None,
):
    return await crud.get_prices_by_item(
        db,
        item_id=item_id,
        limit=limit,
        enchant_level=enchant_level,
        currency=currency,
    )

async def get_latest_price(
    db: AsyncSession,
    item_id: int,
    enchant_level: Optional[int] = None,
    currency: Optional[str] = None,
):
    return await crud.get_latest_price(
        db,
        item_id=item_id,
        enchant_level=enchant_level,
        currency=currency,
    )