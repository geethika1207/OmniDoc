from passlib.context import CryptContext  # just importing hashing library
from jose import jwt, JWTError
from .config import settings
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db.database import get_db
from ..db import models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  
Ouath_scheme = OAuth2PasswordBearer(tokenUrl='login')

def hash_password(password:str):
    return pwd_context.hash(password)

def to_verify(normal_password,hashed_password):
    return pwd_context.verify(normal_password,hashed_password)

ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_EXPIRETIME_MINUTES = settings.ACCESS_EXPIRETIME_MINUTES
def create_token(data:dict):
    to_encode = data.copy()
    expire_time = datetime.utcnow() + timedelta(minutes=ACCESS_EXPIRETIME_MINUTES)
    to_encode.update({"expire_time": expire_time.timestamp()})
    encoded_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM) 
    return encoded_token

def verify_token(token:str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id = payload.get("user_id")
        if id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return id

async def get_current_user(
    token: str = Depends(Ouath_scheme),
    db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="INVALID CREDENTIALS",
        headers={"WWW-Authenticate": "Bearer"}
    )

    userid = verify_token(token, credentials_exception)

    result = await db.execute(
        select(models.USER).where(models.USER.id == userid)
    )

    current_user = result.scalar_one_or_none()

    if current_user is None:
        raise credentials_exception

    return current_user