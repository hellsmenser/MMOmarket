import asyncio
from collections import deque, defaultdict
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.schemas.price import PriceCreate
from app.services.items import get_top_active_items
from app.telegram.classifier import classify_from_history
from app.telegram.client import client, start_client, close_client
from app.telegram.parser import parse_price_message
from app.db.crud.item import get_item_by_name
from app.db.crud.price import add_prices_batch, get_latest_prices_for_classification
from app.core.db import get_async_session
from app.services.prices import get_coin_price
from app.core.redis import get_redis_client, clear_cache
from app.core import logger

logger = logger.get_logger(__name__)

BOT_USERNAME = "forgame_bot"
BATCH_SIZE = 100
PARTIAL_SAVE_SIZE = 2500


async def fetch_and_store_messages():
    try:
        await start_client()
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.error("Cannot start Telegram client. Skipping.")
        return

    try:
        unread_count = await get_undead_count()
        if unread_count == 0:
            logger.info("No new unread messages")
            return
        logger.info(f"Fetching {unread_count} unread messages from {BOT_USERNAME}")

        entity = await client.get_entity(BOT_USERNAME)
        offset_id = 0
        fetched = 0
        parsed_batch: list[PriceCreate] = []
        total_saved = 0
        last_processed_msg_id: int | None = None

        async def flush_prices(session: AsyncSession):
            nonlocal total_saved

            if not parsed_batch:
                return

            logger.info("Classifing...")
            await classify_prices(session, parsed_batch)
            logger.info("Adding into Db...")
            await add_prices_batch(session, parsed_batch)
            await client.send_read_acknowledge(entity, max_id=last_processed_msg_id)

            total_saved += len(parsed_batch)
            logger.info(f"✅ Saved {total_saved}.")

            parsed_batch.clear()

        async for session in get_async_session():
            while fetched < unread_count:
                remaining = unread_count - fetched
                limit = min(BATCH_SIZE, remaining)
                batch_msgs = await client.get_messages(BOT_USERNAME, limit=limit, offset_id=offset_id)
                if not batch_msgs:
                    break
                fetched += len(batch_msgs)
                offset_id = min(msg.id for msg in batch_msgs)
                batch_msgs = sorted(batch_msgs, key=lambda m: m.id)

                for msg in batch_msgs:
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
                    price_obj = PriceCreate(item=item, **parsed, timestamp=msg.date)
                    last_processed_msg_id = msg.id
                    parsed_batch.append(price_obj)

                # Flush if batch size reached or all fetched
                if parsed_batch and (len(parsed_batch) >= PARTIAL_SAVE_SIZE or fetched >= unread_count):
                    await flush_prices(session)

            await client.send_read_acknowledge(entity, max_id=batch_msgs[-1].id if batch_msgs else None)
            redis = await get_redis_client()
            await clear_cache(redis)
            await get_top_active_items(session)
            break

        logger.info(f"📦 Finished. Total saved: {total_saved}")
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.exception(f"fetch_and_store_messages error: {e}")


async def get_undead_count():
    dialogs = await client.get_dialogs()
    unread_count = 0
    for d in dialogs:
        if getattr(d.entity, "username", None) == BOT_USERNAME:
            unread_count = d.unread_count or 0
            break
    return unread_count


async def classify_prices(session: AsyncSession, prices: list[PriceCreate], buffer_size: int = 10):
    buffer: dict[int, deque[int]] = {}
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

        if price.source == "private_trade" and item.category.name == "Доспехи":
            continue

        use_coin_buffer = True
        if price.currency == "coin":
            if (price.item.id, price.currency) != (current_item_id, current_currency):
                history = await get_latest_prices_for_classification(session, price.item.id, price.currency, mods,
                                                                     buffer_size)
                buffer = build_buffer(history, buffer_size)
                current_item_id = price.item.id
                current_currency = price.currency
            empty_mods = [mod for mod in mods if len(buffer[mod]) == 0]
            if empty_mods:
                coin_history = await get_coin_price(session, price.timestamp)
                if coin_history:
                    coin_to_adena = coin_history.coin_price
                    adena_history = await get_latest_prices_for_classification(session, price.item.id, "adena", mods,
                                                                               buffer_size)
                    adena_buffer = build_buffer(adena_history, buffer_size)
                    try:
                        adena_price = price.price * coin_to_adena
                        mod_guess = classify_from_history(
                            PriceCreate(item=price.item, price=adena_price, currency="adena",
                                        timestamp=price.timestamp),
                            adena_buffer, tolerance=item.tolerance)
                        price.enchant_level = str(mod_guess)
                        buffer.setdefault(mod_guess, deque(maxlen=buffer_size)).append(price.price)
                        use_coin_buffer = False
                    except Exception as e:
                        logger.error(f"Error classifying price for item {item.name} (coin->adena): {e}")
                        mod_guess = None
                        price.enchant_level = str(mod_guess)
        if use_coin_buffer:
            if (price.item.id, price.currency) != (current_item_id, current_currency):
                history = await get_latest_prices_for_classification(session, price.item.id, price.currency, mods,
                                                                     buffer_size)
                buffer = build_buffer(history, buffer_size)
                current_item_id = price.item.id
                current_currency = price.currency
            try:
                mod_guess = classify_from_history(price, buffer, tolerance=item.tolerance)
            except Exception as e:
                logger.error(f"Error classifying price for item {item.name}: {e}")
                logger.error(f"{item}")
                mod_guess = None
            price.enchant_level = str(mod_guess)
            if isinstance(mod_guess, int):
                buffer.setdefault(mod_guess, deque(maxlen=buffer_size)).append(price.price)


def build_buffer(history, buffer_size=10):
    buffer = defaultdict(lambda: deque(maxlen=buffer_size))
    for mod, val in history:
        buffer[mod].append(val)
    return buffer
