import asyncio

from app.telegram.service import fetch_and_store_messages
from app.core import logger

logger = logger.get_logger(__name__)

collect_prices_task = None
async def collect_prices():
    try:
        await fetch_and_store_messages()
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.exception(f"collect_prices error: {e}")

def start_collect_prices():
    loop = asyncio.get_event_loop()
    global collect_prices_task
    if collect_prices_task is None or collect_prices_task.done():
        collect_prices_task = loop.create_task(collect_prices())
        return True
    return False
