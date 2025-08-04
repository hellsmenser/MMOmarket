import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime

LOGS_DIR = "logs"

def setup_logging():
    os.makedirs(LOGS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    info_log = os.path.join(LOGS_DIR, f"info_{timestamp}.log")
    error_log = os.path.join(LOGS_DIR, f"error_{timestamp}.log")

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler for INFO and WARNING
    info_handler = RotatingFileHandler(
        info_log, maxBytes=500_000, backupCount=5, encoding="utf-8"
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)
    info_handler.addFilter(lambda record: record.levelno < logging.ERROR)

    # Handler for ERROR and CRITICAL
    error_handler = RotatingFileHandler(
        error_log, maxBytes=500_000, backupCount=5, encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[console_handler, info_handler, error_handler]
    )

    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.info("✓ Логгирование настроено")

