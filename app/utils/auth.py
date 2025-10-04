from fastapi import Request, HTTPException, status
import inspect

from app.config import security

async def auth_or_403(request: Request):
    fn = security.access_token_required
    try:
        if inspect.iscoroutinefunction(fn):
            return await fn(request)
        return fn(request)
    except HTTPException as e:
        if e.status_code in (401, 403):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authenticated")
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authenticated")
