from telethon.sync import TelegramClient

from app.config import get_tg_api_id, get_tg_api_hash

session_name = 'session'
api_id = get_tg_api_id()
api_hash = get_tg_api_hash()
with TelegramClient(session_name, api_id, api_hash) as client:
    print(f"session '{session_name}.session' created.")