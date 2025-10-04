from fastapi import APIRouter, Depends
from app.api import items, prices, categories, controls, auth
from app.utils.auth import auth_or_403

api_router = APIRouter()
api_router.include_router(
    items.router,
    prefix="/items",
    tags=["Items"],
    dependencies=[Depends(auth_or_403)]
)
api_router.include_router(
    prices.router,
    prefix="/prices",
    tags=["Prices"],
    dependencies=[Depends(auth_or_403)]
)
api_router.include_router(
    categories.router,
    prefix="/categories",
    tags=["Сategories"],
    dependencies=[Depends(auth_or_403)]
)
api_router.include_router(
    controls.router,
    prefix="/controls",
    tags=["Controls"],
    dependencies=[Depends(auth_or_403)]
)
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
