from fastapi import Request, HTTPException, status, Response, Depends
import inspect

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import security, config
from app.core.db import get_async_session
from app.db.crud.user import get_user_by_id


async def auth_or_403(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_session),
):
    if request.method == "OPTIONS":
        return None

    fn = security.access_token_required
    try:
        if inspect.iscoroutinefunction(fn):
            user_claims = await fn(request)
        else:
            user_claims = fn(request)

        try:
            user_id = int(user_claims.sub)
        except (AttributeError, TypeError, ValueError):
            response.delete_cookie(
                key=config.JWT_ACCESS_COOKIE_NAME,
                httponly=True,
                secure=config.JWT_COOKIE_SECURE,
                samesite=config.JWT_COOKIE_SAMESITE,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authenticated",
            )

        db_user = await get_user_by_id(db, user_id)
        if not db_user or not db_user.is_active:
            response.delete_cookie(
                key=config.JWT_ACCESS_COOKIE_NAME,
                httponly=True,
                secure=config.JWT_COOKIE_SECURE,
                samesite=config.JWT_COOKIE_SAMESITE,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authenticated",
            )

        new_token = security.create_access_token(uid=str(db_user.id))
        response.set_cookie(
            key=config.JWT_ACCESS_COOKIE_NAME,
            value=new_token,
            httponly=True,
            secure=config.JWT_COOKIE_SECURE,
            samesite=config.JWT_COOKIE_SAMESITE,
            max_age=config.JWT_ACCESS_TOKEN_EXPIRES,
        )

        return user_claims

    except HTTPException as e:
        if e.status_code in (401, 403):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authenticated",
            )
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated",
        )