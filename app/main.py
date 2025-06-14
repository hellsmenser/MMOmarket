from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from app.api.router import api_router
from app.core.db import init_db
from app.core.logger import setup_logging
from app.telegram.service import fetch_and_store_messages

setup_logging()
app = FastAPI(
    title="L2 Market API",
    description="Userbot-based Telegram price tracker",
    version="0.1.0"
)
scheduler = AsyncIOScheduler()

app.include_router(api_router)

@app.on_event("startup")
async def on_startup():
    await init_db()
    await fetch_and_store_messages()
    scheduler.add_job(fetch_and_store_messages, "interval", hours=1)
    scheduler.start()
