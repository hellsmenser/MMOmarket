from redis import RedisError
from redis.asyncio import Redis

from app.config import get_redis_host, get_redis_port, get_redis_db, get_redis_password
import functools
import json
from typing import Callable

from app.utils import tools

_redis_client: Redis | None = None


async def startup_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis(
            host=get_redis_host(),
            port=get_redis_port(),
            db=get_redis_db(),
            password=get_redis_password(),
            decode_responses=True,
        )


async def get_redis_client() -> Redis:
    global _redis_client
    if _redis_client is None:
        await startup_redis()
    try:
        await _redis_client.ping()
    except ConnectionError:
        await startup_redis()
    return _redis_client


def redis_cache(ttl: int = 7200, model=None, is_list=False, exclude_keys=("db", "session")):
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            filtered_kwargs = {k: v for k, v in kwargs.items() if k not in exclude_keys}
            call_data = f"{json.dumps(args, default=str)}:{json.dumps(filtered_kwargs, default=str)}"
            md5 = tools.get_md5_hash(call_data)
            key = f"cache:{func.__name__}:{md5}"

            try:
                client = await get_redis_client()
                cached = await client.get(key)
                if cached is not None:
                    data = json.loads(cached)
                    if model:
                        if data is None:
                            return [] if is_list else None
                        if isinstance(data, list):
                            return [model.model_validate(item) for item in data]
                        return model.model_validate(data)
                    return data
            except RedisError:
                pass

            result = await func(*args, **kwargs)

            try:
                if model:
                    if result is None:
                        return [] if is_list else None
                    if isinstance(result, list):
                        serializable = [item.model_dump() if hasattr(item, 'model_dump') else item for item in result]
                    else:
                        serializable = result.model_dump() if hasattr(result, 'model_dump') else result
                else:
                    serializable = result
                client = await get_redis_client()
                await client.set(key, json.dumps(serializable, default=str), ex=ttl)
            except RedisError:
                pass

            return result if result is not None else ([] if is_list else None)

        return wrapper

    return decorator

async def clear_cache(redis):
    cursor = b"0"
    pattern = "cache:*"
    while cursor:
        cursor, keys = await redis.scan(cursor=cursor, match=pattern, count=500)
        if keys:
            await redis.unlink(*keys)
