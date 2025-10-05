import time
from datetime import datetime, timedelta, date
from typing import List, Optional
from sqlalchemy import select, desc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.price import PriceHistory
from app.db.schemas.price import PriceCreate
import numpy as np


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


def iqr_filter(prices):
    if len(prices) < 4:
        return prices
    arr = np.array(prices)
    q1 = np.percentile(arr, 25)
    q3 = np.percentile(arr, 75)
    iqr = q3 - q1
    filtered = arr[(arr >= q1 - 1.5 * iqr) & (arr <= q3 + 1.5 * iqr)]
    # Additionally: filter values that differ from the median by more than 3 times
    med = np.median(filtered) if len(filtered) > 0 else np.median(arr)
    filtered = filtered[np.abs(filtered - med) <= 3 * med]
    return filtered.tolist() if len(filtered) > 0 else arr.tolist()


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
        modification: Optional[str] = None
) -> list:
    from collections import defaultdict
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period)
    PH = PriceHistory

    # Get all records for the period in a single query
    base_query = select(
        PH.price,
        PH.currency,
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
    base_query = base_query.order_by(func.date(PH.timestamp), PH.currency)
    result = await db.execute(base_query)
    rows = result.mappings().all()

    # Group by day and currency
    grouped = defaultdict(
        lambda: {"timestamp": None, "adena": None, "coin": None, "_prices": {"adena": [], "coin": []}})
    for row in rows:
        day = row["day"]
        currency = row["currency"]
        price = int(row["price"])
        grouped[day]["timestamp"] = day
        grouped[day]["_prices"][currency].append(price)

    result = []
    for day, data in grouped.items():
        for currency in ("adena", "coin"):
            prices = data["_prices"][currency]
            filtered = iqr_filter(prices)
            avg = int(sum(filtered) / len(filtered)) if filtered else (
                int(sum(prices) / len(prices)) if prices else None)
            min_v = min(filtered) if filtered else (min(prices) if prices else None)
            volume = len(prices)
            data[currency] = {
                "avg": avg,
                "min": min_v,
                "volume": volume
            }
        del data["_prices"]
        result.append(data)
    return sorted(result, key=lambda x: x["timestamp"])


async def get_set_price_history():
    pass


async def get_coin_price(db: AsyncSession, to_date: Optional[datetime] = None, aggregate: str = "avg") -> Optional[int]:
    from collections import defaultdict
    PH = PriceHistory
    # Get all records for item_id=793, currency='adena' up to to_date (or today)
    if to_date is None:
        to_date = datetime.utcnow()
    base_query = select(
        PH.price,
        func.date(PH.timestamp).label("day")
    ).where(
        PH.item_id == 793,
        PH.currency == "adena",
        PH.timestamp <= to_date,
        PH.price > 10
    )
    base_query = base_query.order_by(func.date(PH.timestamp))
    result = await db.execute(base_query)
    rows = result.mappings().all()
    # Group by day
    grouped = defaultdict(list)
    for row in rows:
        day = row["day"]
        price = int(row["price"])
        grouped[day].append(price)
    # Aggregate by the last day with data
    if not grouped:
        return None
    last_day = max(grouped.keys())
    prices = grouped[last_day]

    filtered = iqr_filter(prices)
    if filtered:
        return int(sum(filtered) / len(filtered)) if aggregate == "avg" else min(filtered)
    return int(sum(prices) / len(prices)) if aggregate == "avg" else min(prices)


async def get_coin_price_on_day(db: AsyncSession, day: date, aggregate: str = "avg") -> Optional[int]:
    PH = PriceHistory
    base_query = select(
        PH.price
    ).where(
        PH.item_id == 793,
        PH.currency == "adena",
        func.date(PH.timestamp) == day,
        PH.price > 10
    )
    result = await db.execute(base_query)
    prices = [int(row[0]) for row in result.fetchall()]

    filtered = iqr_filter(prices)
    if filtered:
        return int(sum(filtered) / len(filtered)) if aggregate == "avg" else min(filtered)
    if prices:
        return int(sum(prices) / len(prices)) if aggregate == "avg" else min(prices)
    return None
