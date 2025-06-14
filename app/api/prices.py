from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.db import get_async_session
from app.db.schemas.price import PriceCreate, PriceOut
from app.services import prices as service


router = APIRouter()


@router.post("/batch", response_model=List[PriceOut])
async def add_prices(
    prices: List[PriceCreate],
    db: AsyncSession = Depends(get_async_session)
):
    return await service.add_prices_batch(db, prices)


@router.get("/", response_model=List[PriceOut])
async def list_prices(
    item_id: int = Query(..., description="ID предмета"),
    limit: int = Query(100, le=1000),
    enchant_level: Optional[int] = Query(None),
    currency: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_session)
):
    return await service.get_prices_by_item(
        db,
        item_id=item_id,
        limit=limit,
        enchant_level=enchant_level,
        currency=currency,
    )


@router.get("/latest", response_model=Optional[PriceOut])
async def get_latest(
    item_id: int = Query(...),
    enchant_level: Optional[int] = Query(None),
    currency: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_session)
):
    return await service.get_latest_price(
        db,
        item_id=item_id,
        enchant_level=enchant_level,
        currency=currency,
    )
