from fastapi import APIRouter, Depends, Query, Path, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Literal

from app.core.db import get_async_session
from app.db.schemas.price import PriceHistory
from app.services import prices as service


router = APIRouter()


@router.get("/coin", response_model=PriceHistory)
async def get_coin_price(
    db: AsyncSession = Depends(get_async_session),
    aggregate: str = Query("avg", description="Aggregation method for coin price. avg/min")
):
    coin_price = await service.get_coin_price_on_day(db, aggregate)
    if not coin_price:
        raise HTTPException(status_code=404, detail="Coin price not found")

    return coin_price

@router.get("/{item_id}", response_model=List[PriceHistory])
async def get_item_price_history(
    item_id: int = Path(..., gt=0),
    period: int | Literal["all"] = Query(default=30, description="Price history period in days"),
    modification: str = Query(None, description="Modification to include in price history"),
    aggregate: str = Query("avg", description="Aggregation method for price history. avg/min"),
    db: AsyncSession = Depends(get_async_session)
):
    prices = await service.get_item_price_history(db, item_id, period, modification, aggregate)
    if not prices:
        raise HTTPException(status_code=404, detail="Item not found")

    return prices
