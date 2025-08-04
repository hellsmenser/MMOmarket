import redis.asyncio as redis
from app.config import get_redis_host, get_redis_port, get_redis_db, get_redis_password
import functools
import json
from typing import Callable

_redis_client = None


async def startup_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=get_redis_host(),
            port=get_redis_port(),
            db=get_redis_db(),
            password=get_redis_password(),
            decode_responses=True
        )


async def get_redis_client():
    global _redis_client
    if _redis_client is None:
        await startup_redis()
    return _redis_client


def redis_cache(ttl: int = 7200, model=None, exclude_keys=("db", "session")):
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            filtered_kwargs = {k: v for k, v in kwargs.items() if k not in exclude_keys}
            key = f"{func.__name__}:{json.dumps(args, default=str)}:{json.dumps(filtered_kwargs, default=str)}"
            client = await get_redis_client()
            cached = await client.get(key)
            if cached is not None:
                data = json.loads(cached)
                if model:
                    if isinstance(data, list):
                        return [model.model_validate(item) for item in data]
                    return model.model_validate(data)
                return data
            result = await func(*args, **kwargs)
            if model:
                if isinstance(result, list):
                    serializable = [item.model_dump() if hasattr(item, 'model_dump') else item for item in result]
                else:
                    serializable = result.model_dump() if hasattr(result, 'model_dump') else result
            else:
                serializable = result
            await client.set(key, json.dumps(serializable, default=str), ex=ttl)
            return result
        return wrapper
    return decorator

