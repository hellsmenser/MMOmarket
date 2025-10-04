from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
import re

from sqlalchemy.orm import selectinload

from app.db.models import PriceHistory, Category
from app.db.models.item import Item
from app.db.models.item_fts import ItemFTS
from app.db.schemas.item import ItemCreate, ItemUpdate
from app.db.crud.utilits import get_quartiled_query, get_iqr_query


def sanitize_fts_query(user_input: str) -> str:
    cleaned = re.sub(r'["`*\\<>:|&~]', ' ', user_input)
    cleaned = re.sub(r'\s+', ' ', cleaned.strip())

    if not re.fullmatch(r'[\w\s]+', cleaned):
        return ""

    tokens = cleaned.split()
    quoted = [f'"{token}"*' for token in tokens]

    return " ".join(quoted)


async def create_item(db: AsyncSession, item_in: ItemCreate) -> Item:
    db_item = Item(
        name=item_in.name,
        category_id=item_in.category_id,
        _modifications=",".join(str(m) for m in (item_in.modifications or []))
    )
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item


async def get_item(db: AsyncSession, item_id: int):
    result = await db.execute(
        select(Item)
        .options(
            selectinload(Item.category)
        )
        .where(Item.id == item_id)
    )
    return result.scalar_one_or_none()


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
    item = await get_item(db, item_id)
    if not item:
        return None

    if item_in.name is not None:
        item.name = item_in.name
    if item_in.modifications is not None:
        item.modifications = ",".join(str(m) for m in item_in.modifications)
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
    fts_query = sanitize_fts_query(query)
    if not fts_query:
        return []

    offset = (page - 1) * page_size
    fts_stmt = (
        select(ItemFTS.rowid)
        .where(ItemFTS.name.match(fts_query))
        .offset(offset)
        .limit(page_size)
    )
    fts_result = await db.execute(fts_stmt)
    item_ids = [row[0] for row in fts_result.all()]
    if not item_ids:
        return []

    items_stmt = select(Item).where(Item.id.in_(item_ids))
    result = await db.execute(items_stmt)
    return result.scalars().all()


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
