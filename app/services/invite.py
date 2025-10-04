import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud.invite import create_invite_code as crud_create_invite_code
from app.db.crud.invite import get_invite_code_by_code as crud_get_invite_code_by_code
from app.db.crud.invite import mark_invite_code_as_used as crud_mark_invite_code_as_used
from app.db.schemas.auth import InviteCodeResponse


async def generate_invite_code(db: AsyncSession) -> InviteCodeResponse:
    invite_code = str(uuid.uuid4())
    await crud_create_invite_code(db, invite_code)
    return InviteCodeResponse(invite_code=invite_code)


async def validate_invite_code(db: AsyncSession, code: str) -> bool:
    invite_code = await crud_get_invite_code_by_code(db, code)
    return invite_code and not invite_code.used


async def use_invite_code(db: AsyncSession, code: str) -> bool:
    invite_code = await crud_get_invite_code_by_code(db, code)
    if invite_code:
        await crud_mark_invite_code_as_used(db, invite_code.id)
        return True
    return False
