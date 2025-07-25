from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_async_session
from app.db.schemas.category import CategoryRead, CategoryCreate, CategoryShort
from app.services import cateroties as service

router = APIRouter()

@router.get("/", response_model=list[CategoryShort])
async def list_categories(session: AsyncSession = Depends(get_async_session)):
    return await service.get_all(session)

@router.post("/", response_model=CategoryRead)
async def create_category(data: CategoryCreate, session: AsyncSession = Depends(get_async_session)):
    return await service.create(session, data)
