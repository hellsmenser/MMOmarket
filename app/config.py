from datetime import timedelta

from dotenv import load_dotenv
import os
from functools import lru_cache
from authx import AuthX, AuthXConfig

load_dotenv()


def get_tg_api_id() -> int:
    return int(os.getenv("TG_API_ID"))


def get_tg_api_hash() -> str:
    return os.getenv("TG_API_HASH")


def get_tg_session_name() -> str:
    return os.getenv("TG_SESSION_NAME", "default_session")


def get_env() -> str:
    env = os.getenv("ENV", "dev").lower()
    if env not in ["dev", "prod"]:
        raise ValueError(f"Invalid environment: {env}")
    return env


def is_production() -> bool:
    return get_env() == "prod"


def get_redis_host() -> str:
    return os.getenv("REDIS_HOST", "localhost")


def get_redis_port() -> int:
    return int(os.getenv("REDIS_PORT", 6379))


def get_redis_db() -> int:
    return int(os.getenv("REDIS_DB", 0))


def get_redis_password() -> str | None:
    return os.getenv("REDIS_PASSWORD", None)


def get_x_secret_key() -> str:
    return os.getenv("X_SECRET_KEY")


def get_session_key() -> str:
    return os.getenv("SESSION_KEY")


def get_database_url() -> str:
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB")

    if not all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_DB]):
        raise RuntimeError("POSTGRES_* переменные окружения обязательны")

    return f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"


origins_map = {
    "production": [
        "https://hellsmenser.github.io"
    ],
    "development": ["http://127.0.0.1:5173", "http://localhost:5173"]
}


@lru_cache()
def get_authx() -> AuthX:
    cfg = AuthXConfig()
    cfg.JWT_SECRET_KEY = get_session_key()
    cfg.JWT_ACCESS_COOKIE_NAME = "MMOMarket_Access_Cookie"
    cfg.JWT_TOKEN_LOCATION = ["cookies"]
    cfg.JWT_COOKIE_SAMESITE = "none"
    cfg.JWT_COOKIE_SECURE = True
    cfg.JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=3)
    return AuthX(cfg)


security: AuthX = get_authx()
config: AuthXConfig = security.config
