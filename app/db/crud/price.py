from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.price import PriceHistory
from app.db.schemas.price import PriceCreate


async def add_prices_batch(
    db: AsyncSession, prices: List[PriceCreate]
) -> List[PriceHistory]:
    db_prices = [
        PriceHistory(
            item_id=price.item.id,
            price=price.price,
            enchant_level=price.enchant_level,
            currency=price.currency,
            source=price.source,
            timestamp=price.timestamp
        )
        for price in prices
    ]
    db.add_all(db_prices)
    await db.commit()

    for p in db_prices:
        await db.refresh(p)

    return db_prices


async def get_prices_by_item(
    db: AsyncSession,
    item_id: int,
    limit: int = 100,
    enchant_level: Optional[str] = None,
    currency: Optional[str] = None,
) -> List[PriceHistory]:
    stmt = select(PriceHistory).where(PriceHistory.item_id == item_id)

    if enchant_level is not None:
        stmt = stmt.where(PriceHistory.enchant_level == enchant_level)

    if currency is not None:
        stmt = stmt.where(PriceHistory.currency == currency)

    stmt = stmt.order_by(desc(PriceHistory.timestamp)).limit(limit)

    result = await db.execute(stmt)
    return result.scalars().all()

async def get_latest_price(
    db: AsyncSession,
    item_id: int,
    enchant_level: Optional[int] = None,
    currency: Optional[str] = None,
) -> Optional[PriceHistory]:
    prices = await get_prices_by_item(
        db, item_id=item_id, limit=1, enchant_level=enchant_level, currency=currency
    )
    return prices[0] if prices else None

async def get_latest_prices_for_classification(
    session: AsyncSession,
    item_id: int,
    currency: str,
    mods: list[int],
    per_mod_limit: int = 3
) -> list[tuple[int, int]]:
    prices = []
    for mod in mods:
        stmt = (
            select(PriceHistory.enchant_level, PriceHistory.price)
            .where(
                PriceHistory.item_id == item_id,
                PriceHistory.currency == currency,
                PriceHistory.enchant_level == mod
            )
            .order_by(desc(PriceHistory.timestamp))
            .limit(per_mod_limit)
        )
        result = await session.execute(stmt)
        prices.extend([(int(row[0]), row[1]) for row in result.fetchall()])

    return prices
