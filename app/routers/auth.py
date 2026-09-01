import uuid
from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..db.database import get_db
from ..schemas import user
from ..core import security
from ..db import models

router = APIRouter()


@router.post(
    "/user",
    status_code=status.HTTP_201_CREATED,
    response_model=user.UserResponse
)
async def create_user(
    user_credentials: user.UserRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        hashed_password = security.hash_password(user_credentials.password)
        new_user = models.User(
            id=str(uuid.uuid4()),
            email=user_credentials.email,
            hashed_password=hashed_password
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )



@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=user.LoginResponse
)
async def login_user(
    user_credentials: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(models.User).where(
            models.User.email == user_credentials.username
        )
    )
    user_info = result.scalar_one_or_none()

    if not user_info or not security.to_verify(user_credentials.password, user_info.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Credentials"
        )

    access_token = security.create_token({"user_id": user_info.id})

    return {
        "access_token": access_token,
        "token_type": "Bearer"
    }