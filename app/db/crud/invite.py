from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.db.models import InviteCode


async def create_invite_code(db: AsyncSession, code: str):
    db_invite_code = InviteCode(code=code)
    db.add(db_invite_code)
    await db.commit()
    await db.refresh(db_invite_code)
    return db_invite_code


async def get_invite_code_by_code(db: AsyncSession, code: str):
    result = await db.execute(select(InviteCode).where(InviteCode.code == code))
    return result.scalar_one_or_none()


async def mark_invite_code_as_used(db: AsyncSession, invite_code_id: int):
    code = await db.execute(select(InviteCode).where(InviteCode.id == invite_code_id))
    code = code.scalar_one_or_none()
    if code:
        code.used = True
        code.used_at = datetime.now()
        await db.commit()
        await db.refresh(code)
    return code
