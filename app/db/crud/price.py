from datetime import datetime, timedelta, date
from typing import List, Optional
from sqlalchemy import select, desc, Date, cast, func, or_, case, over, true, literal
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud.utilits import get_quartiled_query, get_iqr_query
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

async def get_item_price_history(
    db: AsyncSession,
    item_id: int,
    period: int,
    modification: Optional[str] = None,
    aggregate: str = "avg"
) -> list:
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period)

    PH = PriceHistory

    base_query = select(
        PH.id,
        PH.item_id,
        PH.price,
        PH.currency,
        PH.timestamp,
        func.date(PH.timestamp).label("day")
    ).where(
        PH.item_id == item_id,
        PH.timestamp >= start_date,
        PH.timestamp <= end_date,
        PH.price > 10,
        or_(PH.enchant_level == None, PH.enchant_level != "Сет")
    )

    if modification is not None:
        base_query = base_query.where(PH.enchant_level == modification)

    quartiled = get_quartiled_query(
        base_query,
        partition_by=[PH.item_id, PH.currency, func.date(PH.timestamp)],
        order_by=PH.price
    ).cte("quartiled")

    iqr = get_iqr_query(
        quartiled,
        q_label="quartile",
        price_col="price"
    ).add_columns(
        quartiled.c.day,
        quartiled.c.currency
    ).group_by(quartiled.c.day, quartiled.c.currency).cte("iqr")

    filtered = (
        select(
            quartiled.c.day,
            quartiled.c.currency,
            quartiled.c.price
        )
        .join(iqr, (iqr.c.day == quartiled.c.day) & (iqr.c.currency == quartiled.c.currency))
        .where(
            quartiled.c.price.between(
                iqr.c.q1 - 1.5 * (iqr.c.q3 - iqr.c.q1),
                iqr.c.q3 + 1.5 * (iqr.c.q3 - iqr.c.q1),
            )
        )
        .cte("filtered_prices")
    )

    stmt = select(
        filtered.c.day,
        filtered.c.currency,
        (func.avg(filtered.c.price) if aggregate == "avg" else func.min(filtered.c.price)).label("price")
    ).group_by(filtered.c.day, filtered.c.currency)
    stmt = stmt.order_by(filtered.c.day, filtered.c.currency)

    result = await db.execute(stmt)
    rows = result.mappings().all()

    grouped = {}
    for row in rows:
        day = row["day"]
        currency = row["currency"]
        price = int(row["price"]) if row["price"] is not None else None
        if day not in grouped:
            grouped[day] = {"timestamp": day, "adena": None, "coin": None}
        grouped[day][currency] = price

    return list(grouped.values())

async def get_set_price_history():
    pass

async def get_coin_price(db: AsyncSession, to_date: Optional[datetime] = None, aggregate: str = "avg") -> Optional[int]:
    PH = PriceHistory
    base_query = select(PH.id, PH.price, PH.timestamp).where(
        PH.item_id == 793,
        PH.currency == "adena"
    )
    if to_date:
        base_query = base_query.where(PH.timestamp <= to_date)
    quartiled = get_quartiled_query(base_query, order_by=PH.price).cte("quartiled_coin")
    iqr = get_iqr_query(quartiled).cte("iqr_coin")
    filtered = (
        select(
            quartiled.c.price
        )
        .select_from(quartiled)
        .join(iqr,  literal(True))
        .where(
            quartiled.c.price.between(
                iqr.c.q1 - 1.5 * (iqr.c.q3 - iqr.c.q1),
                iqr.c.q3 + 1.5 * (iqr.c.q3 - iqr.c.q1)
            )
        )
    )
    result = await db.execute(filtered)
    prices = result.scalars().all()
    if not prices:
        return None
    if aggregate == "min":
        return min(prices)
    else:
        return int(sum(prices) / len(prices))

async def get_coin_price_on_day(db: AsyncSession, day: date, aggregate: str = "avg") -> Optional[int]:
    PH = PriceHistory
    base_query = select(PH.id, PH.price, PH.timestamp).where(
        PH.item_id == 793,
        PH.currency == "adena",
        func.date(PH.timestamp) == day
    )
    quartiled = get_quartiled_query(base_query, order_by=PH.price).cte("quartiled_coin_day")
    iqr = get_iqr_query(quartiled).cte("iqr_coin_day")
    filtered = (
        select(
            quartiled.c.price
        )
        .select_from(quartiled)
        .where(
            quartiled.c.price.between(
                iqr.c.q1 - 1.5 * (iqr.c.q3 - iqr.c.q1),
                iqr.c.q3 + 1.5 * (iqr.c.q3 - iqr.c.q1)
            )
        )
    )
    result = await db.execute(filtered)
    prices = result.scalars().all()
    if prices:
        if aggregate == "min":
            return min(prices)
        return int(sum(prices) / len(prices))
    return None
