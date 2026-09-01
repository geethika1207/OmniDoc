from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db.database import get_db
from ..db import models
from .config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def to_verify(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_EXPIRETIME_MINUTES = settings.ACCESS_EXPIRETIME_MINUTES



def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire_time = datetime.utcnow() + timedelta(minutes=ACCESS_EXPIRETIME_MINUTES)
    to_encode.update({"exp": expire_time})  # Standard JWT expiration claim
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)



def verify_token(token: str, credentials_exception) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return user_id



async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    user_id = verify_token(token, credentials_exception)
    result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    current_user = result.scalar_one_or_none()

    if current_user is None:
        raise credentials_exception

    return current_user