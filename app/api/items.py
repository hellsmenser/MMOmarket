from fastapi import APIRouter, Depends, HTTPException, Path, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.db import get_async_session
from app.db.schemas.item import ItemCreate, ItemOut, ItemUpdate, ItemActivity
from app.services import items as service
from app.config import get_x_secret_key

router = APIRouter()


@router.post("/", response_model=ItemOut)
async def add_item(
        item: ItemCreate,
        db: AsyncSession = Depends(get_async_session),
        x_secret_key: str = Header(None, alias="X-secret-key")
):
    secret = get_x_secret_key()
    if not x_secret_key or x_secret_key != secret:
        raise HTTPException(status_code=403, detail="Invalid or missing X-secret-key")
    return await service.create_item(db, item)


@router.get("/", response_model=List[ItemOut])
async def list_items(
        db: AsyncSession = Depends(get_async_session),
        page: int = Query(1, ge=1, description="Page number for pagination"),
        page_size: int = Query(20, ge=1, le=100, description="Number of items per page")
):
    return await service.get_items(db, page=page, page_size=page_size)


@router.get("/search", response_model=List[ItemOut])
async def search_items(
        query: str = Query(..., min_length=1),
        db: AsyncSession = Depends(get_async_session),
        page: int = Query(1, ge=1, description="Page number for pagination"),
        page_size: int = Query(20, ge=1, le=100, description="Number of items per page")
):
    items = await service.search_items(db, query, page=page, page_size=page_size)
    if not items:
        raise HTTPException(status_code=404, detail="No items found")
    return items


@router.get("/volatility", response_model=List[ItemActivity])
async def get_top_active_items(
        db: AsyncSession = Depends(get_async_session),
        category_id: int = Query(None, ge=1, description="Filter by category ID")
):
    volatility = await service.get_top_active_items(db=db, category_id=category_id)
    if not volatility:
        raise HTTPException(status_code=404, detail="Items not found")
    return volatility


@router.get("/{item_id}", response_model=ItemOut)
async def get_item_by_id(
        item_id: int = Path(..., gt=0),
        db: AsyncSession = Depends(get_async_session)
):
    item = await service.get_item(db=db, item_id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.patch("/{item_id}", response_model=ItemOut)
async def update_item_by_id(
        item_id: int = Path(..., gt=0),
        item_in: ItemUpdate = ...,
        db: AsyncSession = Depends(get_async_session)
):
    updated = await service.update_item(db=db, item_id=item_id, item_in=item_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated


@router.delete("/{item_id}", status_code=204)
async def delete_item_by_id(
        item_id: int = Path(..., gt=0),
        db: AsyncSession = Depends(get_async_session)
):
    deleted = await service.delete_item(db, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")
