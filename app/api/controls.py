from fastapi import APIRouter

from app.core.redis import get_redis_client
from app.services import controls as service

router = APIRouter()
@router.get("/collect-prices")
async def collect_prices():
    started = service.start_collect_prices()
    if started:
        return {"message": "Price collection started"}
    else:
        return {"message": "Task already running"}

@router.get("/ping-redis")
async def ping():
    redis = await get_redis_client()
    pong = await redis.ping()
    return {"pong": pong}
