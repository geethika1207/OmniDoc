# 1. New imports for async
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from ..core.config import settings 

# 2. Add "+asyncpg" to your connection URL
SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{settings.DATABASE_USERNAME}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOSTNAME}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"

# 3. Create the async engine
engine = create_async_engine(SQLALCHEMY_DATABASE_URL)

# 4. Use async_sessionmaker and include expire_on_commit=False
SessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

# 5. Convert the dependency to async
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close() 