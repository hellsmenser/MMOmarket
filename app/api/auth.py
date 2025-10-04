from fastapi import APIRouter, Depends, HTTPException, status, Header, Response

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_x_secret_key, config, security
from app.core.db import get_async_session
from app.db.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse, InviteCodeResponse
from app.utils.auth import auth_or_403
from app.services.auth import create_user, authenticate_user
from app.services.invite import generate_invite_code, validate_invite_code, use_invite_code

router = APIRouter()


def verify_api_key(x_secret_key: str = Header(...)):
    if x_secret_key != get_x_secret_key():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    return x_secret_key


@router.post("/generate-invite", response_model=InviteCodeResponse)
async def generate_invite_endpoint(_: str = Depends(verify_api_key),
                                   db: AsyncSession = Depends(get_async_session)):
    invite_code = await generate_invite_code(db)
    return invite_code


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister,
                   db: AsyncSession = Depends(get_async_session)):
    try:
        invite_code_is_valid = await validate_invite_code(db, user_data.invite_code)
        if not invite_code_is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or already used invite code"
            )

        user = await create_user(db, user_data)

        await use_invite_code(db, user_data.invite_code)

        return user
    except ValueError as e:
        # Дубликат имени
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"register error: {str(e)}"
        )


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin,
                db: AsyncSession = Depends(get_async_session),
                response: Response = None):
    try:
        user = await authenticate_user(db, user_data.username, user_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )

        token = security.create_access_token(uid=str(user.id))
        response.set_cookie(
            key=config.JWT_ACCESS_COOKIE_NAME,
            value=token,
            httponly=True,
            secure=config.JWT_COOKIE_SECURE,
            samesite=config.JWT_COOKIE_SAMESITE
        )
        return {"access_token": token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login error",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response):
    response.delete_cookie(
        key=config.JWT_ACCESS_COOKIE_NAME,
        httponly=True,
        secure=config.JWT_COOKIE_SECURE,
        samesite=config.JWT_COOKIE_SAMESITE
    )
    return {"detail": "Logged out"}


@router.get("/me")
async def me(claims = Depends(auth_or_403)):
    return {"authorized": True, "claims": claims}
