from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
import re

from sqlalchemy.orm import selectinload

from app.db.models import PriceHistory, Category
from app.db.models.item import Item
from app.db.schemas.item import ItemCreate, ItemUpdate
from app.db.crud.utilits import get_quartiled_query, get_iqr_query

MIN_FTS_TOKEN_LEN = 3


def sanitize_fts_query(user_input: str) -> str:
    cleaned = re.sub(r'[^\w\s-]+', ' ', user_input).strip()
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned[:120]


def _normalize_query(q: str) -> str:
    q = q.lower()
    q = re.sub(r'[^0-9a-zа-яё\s]+', ' ', q)
    q = re.sub(r'\s+', ' ', q).strip()
    return q


def _split_tokens(q: str) -> list[str]:
    return [t for t in q.split() if t]


def _fts_tokens(tokens: list[str]) -> list[str]:
    return [f"{t}:*" for t in tokens if len(t) >= MIN_FTS_TOKEN_LEN]


async def create_item(db: AsyncSession, item_in: ItemCreate) -> Item:
    db_item = Item(
        name=item_in.name,
        category_id=item_in.category_id,
    )
    if item_in.modifications:
        db_item.modifications = [int(m) for m in item_in.modifications]
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item


async def get_item(db: AsyncSession, item_id: int) -> Optional[Item]:
    stmt = (
        select(Item)
        .options(
            selectinload(Item.category),
        )
        .where(Item.id == item_id)
        .limit(1)
    )
    res = await db.execute(stmt)
    return res.scalars().first()


async def get_item_by_name(db: AsyncSession, item_name: str) -> Optional[Item]:
    stmt = select(Item).options(selectinload(Item.category)).where(Item.name == item_name)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_items(db: AsyncSession, page: int, page_size: int):
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Item)
        .options(
            selectinload(Item.category)
        )
        .offset(offset)
        .limit(page_size)
    )
    return result.scalars().all()


async def update_item(
        db: AsyncSession, item_id: int, item_in: ItemUpdate
) -> Optional[Item]:
    stmt = (
        select(Item)
        .options(
            selectinload(Item.category),
        )
        .where(Item.id == item_id)
        .limit(1)
    )
    res = await db.execute(stmt)
    item = res.scalars().first()
    if not item:
        return None

    if item_in.name is not None:
        item.name = item_in.name
    if item_in.modifications is not None:
        item.modifications = [int(m) for m in item_in.modifications] if item_in.modifications else []
    if item_in.category_id is not None:
        item.category_id = item_in.category_id

    await db.commit()
    await db.refresh(item)
    return item


async def delete_item(
        db: AsyncSession, item_id: int
) -> bool:
    item = await get_item(db, item_id)
    if not item:
        return False
    await db.delete(item)
    await db.commit()
    return True


async def search_items_by_name(db: AsyncSession, query: str, page: int = 1, page_size: int = 20):
    norm = _normalize_query(query)
    if not norm:
        return []
    tokens = _split_tokens(norm)
    if not tokens:
        return []

    offset = (page - 1) * page_size
    fts_parts = _fts_tokens(tokens)

    results_ordered = []
    seen_ids = set()

    if fts_parts:
        tsquery_str = " & ".join(fts_parts)
        tsquery = func.to_tsquery('russian', tsquery_str)
        tsv = Item.search_vector
        fts_stmt = (
            select(Item)
            .options(selectinload(Item.category))
            .where(tsv.op('@@')(tsquery))
            .order_by(func.ts_rank_cd(tsv, tsquery).desc(), Item.id.asc())
            .offset(offset)
            .limit(page_size)
        )
        fts_res = await db.execute(fts_stmt)
        for it in fts_res.scalars().unique():
            results_ordered.append(it)
            seen_ids.add(it.id)

    last_token = tokens[-1]
    last_token_short = len(last_token) < MIN_FTS_TOKEN_LEN
    need_fallback = not results_ordered or last_token_short

    if need_fallback:
        prefix = last_token
        ilike_pattern = f"{prefix}%"
        ilike_stmt = (
            select(Item)
            .options(selectinload(Item.category))
            .where(Item.name.ilike(ilike_pattern))
            .order_by(Item.name.asc())
            .limit(page_size)
        )
        ilike_res = await db.execute(ilike_stmt)
        for it in ilike_res.scalars().unique():
            if it.id not in seen_ids:
                results_ordered.append(it)
                seen_ids.add(it.id)

    return results_ordered[:page_size]


async def get_top_active_items(session: AsyncSession, days: int = 7, limit: int = 15,
                               category_id: Optional[int] = None):
    since = datetime.utcnow() - timedelta(days=days)
    PH = PriceHistory

    base_query = select(
        PH.id,
        PH.item_id,
        PH.price,
        PH.currency,
        PH.timestamp
    ).where(PH.timestamp >= since)

    quartiled = get_quartiled_query(
        base_query,
        partition_by=[PH.item_id],
        order_by=PH.price
    ).cte("quartiled")

    iqr = get_iqr_query(
        quartiled,
        q_label="quartile",
        price_col="price"
    ).add_columns(
        quartiled.c.item_id
    ).group_by(quartiled.c.item_id).cte("iqr")

    filtered = (
        select(
            quartiled.c.id,
            quartiled.c.item_id,
            quartiled.c.price,
            quartiled.c.currency,
            quartiled.c.timestamp
        )
        .join(iqr, iqr.c.item_id == quartiled.c.item_id)
        .where(
            quartiled.c.price.between(
                iqr.c.q1 - 1.5 * (iqr.c.q3 - iqr.c.q1),
                iqr.c.q3 + 1.5 * (iqr.c.q3 - iqr.c.q1),
            )
        )
        .cte("filtered_prices")
    )

    avg_price = func.avg(filtered.c.price).label("avg_price")

    stmt = (
        select(
            Item.id,
            Item.name,
            Category.id,
            Category.name,
            filtered.c.currency,
            func.count(filtered.c.id).label("count"),
            avg_price
        )
        .join(filtered, filtered.c.item_id == Item.id)
        .join(Category, Category.id == Item.category_id)
        .group_by(Item.id, Category.id, filtered.c.currency)
        .order_by(func.count(filtered.c.id).desc())
        .limit(limit)
    )

    if category_id is not None:
        stmt = stmt.where(Item.category_id == category_id)

    result = await session.execute(stmt)
    return result.all()
