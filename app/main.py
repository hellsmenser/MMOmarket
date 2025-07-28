from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.core.db import init_db
from app.core.logger import setup_logging
from app.services import controls

setup_logging()
app = FastAPI(
    title="L2 Market API",
    description="Userbot-based Telegram price tracker",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)
scheduler = AsyncIOScheduler()
origins = [
    "https://hellsmenser.github.io",
    "https://hellsmenser.github.io/MMOMarket-frontend",
]

app.include_router(api_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.on_event("startup")
async def on_startup():
    await init_db()
    scheduler.add_job(controls.collect_prices, "interval", hours=2)
    scheduler.start()
