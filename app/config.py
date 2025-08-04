from dotenv import load_dotenv
import os

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


origins_map = {
    "production": [
        "https://hellsmenser.github.io",
        "https://hellsmenser.github.io/MMOMarket-frontend"
    ],
    "development": ["*"]
}
