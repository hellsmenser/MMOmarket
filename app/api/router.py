from fastapi import APIRouter
from app.api import items, prices, categories, controls

api_router = APIRouter()
api_router.include_router(items.router, prefix="/items", tags=["Items"])
api_router.include_router(prices.router, prefix="/prices", tags=["Prices"])
api_router.include_router(categories.router, prefix="/categories", tags=["Сategories"])
api_router.include_router(controls.router, prefix="/controls", tags=["Controls"])