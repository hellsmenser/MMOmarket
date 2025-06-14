from dotenv import load_dotenv
import os

load_dotenv()
def get_tg_api_id() -> int:
    return int(os.getenv("TG_API_ID"))

def get_tg_api_hash() -> str:
    return os.getenv("TG_API_HASH")

def get_tg_session_name() -> str:
    return os.getenv("TG_SESSION_NAME", "default_session")