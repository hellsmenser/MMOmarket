from collections import deque
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.schemas.price import PriceCreate
from app.telegram.classifier import classify_from_history
from app.telegram.client import client, start_client
from app.telegram.parser import parse_price_message
from app.db.crud.item import get_item_by_name
from app.db.crud.price import add_prices_batch, get_latest_prices_for_classification
from app.core.db import get_async_session
import logging

logger = logging.getLogger(__name__)

BOT_USERNAME = "forgame_bot"
BATCH_SIZE = 10

async def fetch_and_store_messages():
    await start_client()
    unread_count = await get_undead_count()

    if unread_count == 0:
        logger.info("📭 No new unread messages")
        return

    all_messages = []
    offset_id = 0
    fetched = 0

    while fetched < unread_count:
        remaining = unread_count - fetched
        limit = min(BATCH_SIZE, remaining)
        batch = await client.get_messages(BOT_USERNAME, limit=limit, offset_id=offset_id)
        if not batch:
            break
        all_messages.extend(batch)
        fetched += len(batch)
        offset_id = min(msg.id for msg in batch)

    new_unread_count = await get_undead_count()
    if new_unread_count > 0 and new_unread_count != unread_count:
        offset_id = min(msg.id for msg in all_messages)
        batch = await client.get_messages(BOT_USERNAME, limit=new_unread_count, offset_id=offset_id)
        if batch:
            all_messages.extend(batch)

    logger.info(f"📬 Unread messages: {len(all_messages)}")

    all_messages = sorted(all_messages, key=lambda m: m.id)

    async for session in get_async_session():
        parsed_batch = []
        for msg in all_messages:
            if not msg.text:
                continue

            parsed = parse_price_message(msg.text)
            if not parsed:
                logger.warning(f"❌ Failed to parse message: {msg.text}")
                continue

            if parsed["currency"] == "unknown":
                logger.warning(f"❌ Unknown currency in message: {msg.text}")
            item = await get_item_by_name(session, parsed["item_name"])
            if not item:
                logger.warning(f"❌ Unknown item: {parsed['item_name']}")
                continue

            parsed_batch.append({
                "item": item,
                "price": parsed["price"],
                "currency": parsed["currency"],
                "enchant_level": parsed.get("enchant_level"),
                "timestamp": msg.date,
                "source": parsed["source"]
            })

        if parsed_batch:
            price_objs = [PriceCreate(**data) for data in parsed_batch]
            await classify_prices(session, price_objs)
            await add_prices_batch(session, price_objs)
            logger.info(f"✅ Saved {len(parsed_batch)} price entries")

        if all_messages:
            entity = await client.get_entity(BOT_USERNAME)
            last_msg_id = max(msg.id for msg in all_messages)
            await client.send_read_acknowledge(entity, max_id=last_msg_id)

        break

async def get_undead_count():
    dialogs = await client.get_dialogs()
    unread_count = 0
    for d in dialogs:
        if getattr(d.entity, "username", None) == BOT_USERNAME:
            unread_count = d.unread_count or 0
            break
    return unread_count

async def classify_prices(session: AsyncSession, prices: list[PriceCreate], buffer_size: int = 10):
    buffer: deque[tuple[int, int]] = deque(maxlen=buffer_size)
    current_item_id: Optional[int] = None
    current_currency: Optional[str] = None

    prices.sort(key=lambda p: (p.item.name if p.item else '', p.currency or '', p.timestamp))
    for price in prices:
        item = price.item

        if not item or not item.modifications:
            continue
        mods = [int(x) for x in item.modifications if str(x).isdigit()]
        if len(mods) == 1:
            price.enchant_level = str(mods[0])
            continue

        if (price.item.id, price.currency) != (current_item_id, current_currency):
            history = await get_latest_prices_for_classification(session, price.item.id, price.currency, mods, buffer_size)
            buffer = deque(history, maxlen=buffer_size)
            current_item_id = price.item.id
            current_currency = price.currency

        # Классифицируем
        mod_guess = classify_from_history(price, list(buffer), tolerance=item.tolerance)
        price.enchant_level = str(mod_guess)

        if isinstance(mod_guess, int):
            buffer.append((mod_guess, price.price))
