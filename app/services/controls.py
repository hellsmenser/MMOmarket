import asyncio

from app.telegram.service import fetch_and_store_messages

collect_prices_task = None
async def collect_prices():
    await fetch_and_store_messages()

def start_collect_prices():
    loop = asyncio.get_event_loop()
    global collect_prices_task
    if collect_prices_task is None or collect_prices_task.done():
        collect_prices_task = loop.create_task(collect_prices())
        return True
    return False