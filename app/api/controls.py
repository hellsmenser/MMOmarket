from fastapi import APIRouter
from app.services import controls as service

router = APIRouter()
@router.get("/collect-prices")
async def collect_prices():
    started = service.start_collect_prices()
    if started:
        return {"message": "Price collection started"}
    else:
        return {"message": "Task already running"}