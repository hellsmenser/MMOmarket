from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Literal

from app.db.crud import price as crud
from app.db.schemas.price import PriceCreate, PriceHistory
from datetime import date, timedelta
from app.core.redis import redis_cache


async def add_prices_batch(db: AsyncSession, prices: List[PriceCreate]) -> List[PriceCreate]:
    return await crud.add_prices_batch(db, prices)


@redis_cache(ttl=7200, model=PriceHistory)
async def get_item_price_history(
    db: AsyncSession,
    item_id: int,
    period: int | Literal["all"],
    modification: str = None
) -> Optional[List[PriceHistory]]:
    if period == "all":
        period = 90
    items = await crud.get_item_price_history(db, item_id, period, modification)
    if not items:
        return None
    result = []
    for row in items:
        ts = row["timestamp"]
        if hasattr(ts, 'year') and not hasattr(ts, 'hour'):
            from datetime import datetime, time
            ts = datetime.combine(ts, time.min)
        coin_price = None
        coin_price_obj = await crud.get_coin_price_on_day(db, ts)
        if coin_price_obj:
            coin_price = coin_price_obj[0].price if isinstance(coin_price_obj, list) else coin_price_obj
        out = PriceHistory(
            adena_avg=row["adena"]["avg"],
            adena_min=row["adena"]["min"],
            adena_volume=row["adena"]["volume"],
            coin_avg=row["coin"]["avg"],
            coin_min=row["coin"]["min"],
            coin_volume=row["coin"]["volume"],
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
        adena=None,
        coin=None,
        coin_price=coin,
        timestamp=date.today()
    ) if coin else None


async def get_coin_price(
    db: AsyncSession,
    to_date: Optional[str] = None,
    aggregate: str = "avg"
) -> PriceHistory:
    price = await crud.get_coin_price(db, to_date, aggregate)
    if not price:
        return None
    return PriceHistory(
        adena=None,
        coin=None,
        coin_price=price,
        timestamp=date.today()
    )
