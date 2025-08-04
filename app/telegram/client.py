import logging
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

from app.config import get_tg_api_id, get_tg_api_hash, get_tg_session_name

logger = logging.getLogger(__name__)

API_ID = get_tg_api_id()
API_HASH = get_tg_api_hash()
SESSION_NAME = get_tg_session_name()

# Initialize client
client = TelegramClient(
    SESSION_NAME,
    API_ID,
    API_HASH
)


async def start_client():
    if client.is_connected():
        return

    try:
        await client.start()
        me = await client.get_me()
        logger.info(f"✅ Telegram client started as @{me.username or me.first_name}")
    except SessionPasswordNeededError:
        logger.error("❌ Two-factor auth is enabled. Password required.")
        raise
    except Exception as e:
        logger.exception(f"❌ Failed to start Telegram client: {e}")
        raise

async def close_client():
    if client.is_connected():
        await client.disconnect()
        logger.info("✅ Telegram client disconnected")

