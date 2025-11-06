from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Literal
from datetime import date, timedelta, datetime, time

from app.db.crud import price as crud
from app.db.schemas.price import PriceHistory
from app.core.redis import redis_cache


@redis_cache(ttl=7200, model=PriceHistory, is_list=True)
async def get_item_price_history(
    db: AsyncSession,
    item_id: int,
    period: int | Literal["all"],
    modification: str = None
) -> Optional[List[PriceHistory]]:
    if period == "all":
        period = 90
    rows = await crud.get_item_price_history(db, item_id, period, modification)
    if not rows:
        return None

    min_day = min(r["timestamp"] for r in rows)
    max_day = max(r["timestamp"] for r in rows)
    start_day = min_day if isinstance(min_day, date) and not isinstance(min_day, datetime) else min_day.date()
    end_day = max_day if isinstance(max_day, date) and not isinstance(max_day, datetime) else max_day.date()

    coin_map = await crud.get_coin_price_map(db, start_day, end_day, aggregate="avg")

    result: List[PriceHistory] = []
    for row in rows:
        ts = row["timestamp"]
        if isinstance(ts, date) and not isinstance(ts, datetime):
            ts = datetime.combine(ts, time.min)
        coin_price = None
        day_key = ts.date()
        if day_key in coin_map:
            coin_price = coin_map[day_key]
        out = PriceHistory(
            adena_avg=row.get("adena", {}).get("avg") if row.get("adena") else None,
            adena_min=row.get("adena", {}).get("min") if row.get("adena") else None,
            adena_volume=row.get("adena", {}).get("volume") if row.get("adena") else None,
            coin_avg=row.get("coin", {}).get("avg") if row.get("coin") else None,
            coin_min=row.get("coin", {}).get("min") if row.get("coin") else None,
            coin_volume=row.get("coin", {}).get("volume") if row.get("coin") else None,
            coin_price=coin_price,
            timestamp=ts
        )
        result.append(out)
    return result


@redis_cache(ttl=7200, model=PriceHistory)
async def get_coin_price_on_day(
    db: AsyncSession,
    aggregate: str = "avg"
) -> Optional[PriceHistory]:
    coin = await crud.get_coin_price_on_day(db, date.today(), aggregate=aggregate)
    if not coin:
        coin = await crud.get_coin_price_on_day(db, date.today() - timedelta(days=1), "avg")
    return PriceHistory(
        adena_avg=None,
        adena_min=None,
        adena_volume=None,
        coin_avg=None,
        coin_min=None,
        coin_volume=None,
        coin_price=coin,
        timestamp=datetime.combine(date.today(), time.min)
    ) if coin else None


async def get_coin_price(
    db: AsyncSession,
    to_date: Optional[str] = None,
    aggregate: str = "avg"
) -> Optional[PriceHistory]:
    dt_to = None
    if to_date:
        try:
            dt_to = datetime.fromisoformat(to_date)
        except:
            dt_to = None
    price = await crud.get_coin_price(db, dt_to, aggregate)
    if not price:
        return None
    return PriceHistory(
        adena_avg=None,
        adena_min=None,
        adena_volume=None,
        coin_avg=None,
        coin_min=None,
        coin_volume=None,
        coin_price=price,
        timestamp=datetime.combine(date.today(), time.min)
    )
