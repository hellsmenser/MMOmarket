from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.db import get_async_session
from app.db.schemas.item import ItemCreate, ItemOut, ItemUpdate
from app.services import items as service

router = APIRouter()

@router.post("/", response_model=ItemOut)
async def add_item(
    item: ItemCreate,
    db: AsyncSession = Depends(get_async_session)
):
    return await service.create_item(db, item)

@router.get("/", response_model=List[ItemOut])
async def list_items(
    db: AsyncSession = Depends(get_async_session)
):
    return await service.get_items(db)

@router.get("/{item_id}", response_model=ItemOut)
async def get_item_by_id(
    item_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_async_session)
):
    item = await service.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.patch("/{item_id}", response_model=ItemOut)
async def update_item_by_id(
    item_id: int = Path(..., gt=0),
    item_in: ItemUpdate = ...,
    db: AsyncSession = Depends(get_async_session)
):
    updated = await service.update_item(db, item_id, item_in)
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