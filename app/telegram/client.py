from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import asyncio

from app.config import get_tg_api_id, get_tg_api_hash, get_tg_session_name
from app.core import logger

logger = logger.get_logger(__name__)

API_ID = get_tg_api_id()
API_HASH = get_tg_api_hash()
SESSION_NAME = get_tg_session_name()

# Initialize client
client = TelegramClient(
    SESSION_NAME,
    API_ID,
    API_HASH
)

_client_lock = asyncio.Lock()

async def start_client(retries: int = 3):
    if client.is_connected():
        return
    async with _client_lock:
        if client.is_connected():
            return
        for attempt in range(1, retries + 1):
            try:
                await client.start()
                me = await client.get_me()
                logger.info(f"Telegram client started as @{me.username or me.first_name}")
                return
            except SessionPasswordNeededError:
                logger.error("Two-factor auth enabled. Password required.")
                raise
            except asyncio.CancelledError:
                raise
            except Exception as e:
                if attempt == retries:
                    logger.exception(f"Failed to start Telegram client after {attempt} attempts: {e}")
                    return
                delay = attempt * 2
                logger.warning(f"Start attempt {attempt}/{retries} failed: {e}. Retry in {delay}s")
                await asyncio.sleep(delay)

async def close_client():
    if client.is_connected():
        await client.disconnect()
        logger.info("✅ Telegram client disconnected")
