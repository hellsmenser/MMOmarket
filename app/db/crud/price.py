from datetime import datetime, timedelta, date
from typing import List, Optional, Union
from sqlalchemy import select, desc, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.price import PriceHistory, DailyPriceStats
from app.db.schemas.price import PriceCreate
import numpy as np


async def add_prices_batch(
        db: AsyncSession,
        prices: List[PriceCreate],
) -> None:
    if not prices:
        return
    db_prices = [
        PriceHistory(
            item_id=price.item.id,
            price=price.price,
            enchant_level=str(price.enchant_level) if price.enchant_level is not None else None,
            currency=price.currency,
            source=price.source,
            timestamp=price.timestamp
        )
        for price in prices
    ]
    db.add_all(db_prices)
    await db.commit()


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


async def refresh_daily_price_stats(db: AsyncSession, concurrently: bool = True):
    stmt = text("REFRESH MATERIALIZED VIEW {} daily_price_stats".format("CONCURRENTLY" if concurrently else ""))
    await db.execute(stmt)
    await db.commit()


async def get_prices_by_item(
        db: AsyncSession,
        item_id: int,
        limit: int = 100,
        enchant_level: Optional[Union[int, str]] = None,
        currency: Optional[str] = None,
) -> List[PriceHistory]:
    stmt = select(PriceHistory).where(PriceHistory.item_id == item_id)

    if enchant_level is not None:
        stmt = stmt.where(PriceHistory.enchant_level == str(enchant_level))

    if currency is not None:
        stmt = stmt.where(PriceHistory.currency == currency)

    stmt = stmt.order_by(desc(PriceHistory.timestamp)).limit(limit)

    result = await db.execute(stmt)
    return result.scalars().all()


async def get_latest_price(
        db: AsyncSession,
        item_id: int,
        enchant_level: Optional[Union[int, str]] = None,
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
                PriceHistory.enchant_level == str(mod)
            )
            .order_by(desc(PriceHistory.timestamp))
            .limit(per_mod_limit)
        )
        result = await session.execute(stmt)
        prices.extend([(int(row[0]), row[1]) for row in result.fetchall()])

    return prices


async def get_coin_price(db: AsyncSession, to_date: Optional[datetime] = None, aggregate: str = "avg") -> Optional[int]:
    if to_date is None:
        to_date = datetime.utcnow()
    DPS = DailyPriceStats
    stmt = (
        select(DPS.day, DPS.avg_price, DPS.min_price)
        .where(
            DPS.item_id == 793,
            DPS.currency == "adena",
            DPS.day <= func.date_trunc('day', to_date)
        )
        .order_by(DPS.day.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        return None
    avg_price = int(row.avg_price)
    min_price = int(row.min_price)
    return avg_price if aggregate == "avg" else min_price


async def get_coin_price_on_day(db: AsyncSession, day: date, aggregate: str = "avg") -> Optional[int]:
    DPS = DailyPriceStats
    stmt = (
        select(DPS.avg_price, DPS.min_price)
        .where(
            DPS.item_id == 793,
            DPS.currency == "adena",
            DPS.day == day
        )
        .limit(1)
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        return None
    avg_price = int(row.avg_price)
    min_price = int(row.min_price)
    return avg_price if aggregate == "avg" else min_price


async def get_coin_price_map(db: AsyncSession, start: date, end: date, aggregate: str = "avg") -> dict[date, int]:
    DPS = DailyPriceStats
    stmt = (
        select(DPS.day, DPS.avg_price, DPS.min_price)
        .where(
            DPS.item_id == 793,
            DPS.currency == "adena",
            DPS.day >= start,
            DPS.day <= end
        )
        .order_by(DPS.day)
    )
    result = await db.execute(stmt)
    rows = result.fetchall()
    out = {}
    for r in rows:
        avg_price = int(r.avg_price)
        min_price = int(r.min_price)
        out[r.day] = avg_price if aggregate == "avg" else min_price
    return out


async def get_item_price_history(
        db: AsyncSession,
        item_id: int,
        period: int,
        modification: Optional[str] = None
) -> list:
    if modification is not None:
        from collections import defaultdict
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period)
        PH = PriceHistory
        base_query = select(
            PH.price,
            PH.currency,
            func.date(PH.timestamp).label("day")
        ).where(
            PH.item_id == item_id,
            PH.timestamp >= start_date,
            PH.timestamp <= end_date,
            PH.price > 10,
            PH.enchant_level == modification
        ).order_by(func.date(PH.timestamp), PH.currency)
        result = await db.execute(base_query)
        rows = result.mappings().all()
        grouped = defaultdict(lambda: {"timestamp": None, "adena": None, "coin": None, "_prices": {"adena": [], "coin": []}})
        for row in rows:
            day = row["day"]
            currency = row["currency"]
            price = int(row["price"])
            grouped[day]["timestamp"] = day
            grouped[day]["_prices"][currency].append(price)
        out = []
        for day, data in grouped.items():
            for currency in ("adena", "coin"):
                prices = data["_prices"][currency]
                filtered = iqr_filter(prices)
                avg = int(sum(filtered) / len(filtered)) if filtered else (int(sum(prices) / len(prices)) if prices else None)
                min_v = min(filtered) if filtered else (min(prices) if prices else None)
                volume = len(prices)
                data[currency] = {"avg": avg, "min": min_v, "volume": volume}
            del data["_prices"]
            out.append(data)
        return sorted(out, key=lambda x: x["timestamp"])

    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=period)
    DPS = DailyPriceStats
    stmt = (
        select(DPS.day, DPS.currency, DPS.avg_price, DPS.min_price, DPS.volume)
        .where(
            DPS.item_id == item_id,
            DPS.day >= start_date,
            DPS.day <= end_date
        )
        .order_by(DPS.day, DPS.currency)
    )
    result = await db.execute(stmt)
    rows = result.fetchall()

    from collections import defaultdict
    grouped: dict[date, dict] = defaultdict(lambda: {"timestamp": None, "adena": None, "coin": None})
    for r in rows:
        day = r.day
        currency = r.currency
        grouped[day]["timestamp"] = day
        grouped[day][currency] = {
            "avg": int(r.avg_price) if r.avg_price is not None else None,
            "min": int(r.min_price) if r.min_price is not None else None,
            "volume": int(r.volume) if r.volume is not None else None,
        }
    return [grouped[d] for d in sorted(grouped.keys())]
