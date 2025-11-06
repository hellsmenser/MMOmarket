from fastapi import Request, HTTPException, status, Response
import inspect

from app.config import security, config


async def auth_or_403(request: Request, response: Response):
    if request.method == "OPTIONS":
        return None
    fn = security.access_token_required
    try:
        if inspect.iscoroutinefunction(fn):
            user = await fn(request)
        else:
            user = fn(request)

        new_token = security.create_access_token(uid=user.sub)
        response.set_cookie(
            key=config.JWT_ACCESS_COOKIE_NAME,
            value=new_token,
            httponly=True,
            secure=config.JWT_COOKIE_SECURE,
            samesite=config.JWT_COOKIE_SAMESITE,
            max_age=config.JWT_ACCESS_TOKEN_EXPIRES
        )

        return user

    except HTTPException as e:
        if e.status_code in (401, 403):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authenticated"
            )
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated"
        )