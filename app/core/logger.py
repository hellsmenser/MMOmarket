import logging
from logging.handlers import RotatingFileHandler
import os

LOGS_DIR = "logs"
LOG_FILE = os.path.join(LOGS_DIR, "app.log")


def setup_logging():
    os.makedirs(LOGS_DIR, exist_ok=True)

    # Формат логов
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Консольный хендлер
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Файловый хендлер с ротацией
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    # Настройка корневого логгера
    logging.basicConfig(
        level=logging.INFO,
        handlers=[console_handler, file_handler]
    )

    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.info("✓ Логгирование настроено")
