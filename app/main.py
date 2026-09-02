from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text
from .db.database import engine, Base
from .routers import auth, document

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Async database table initialization and pgvector extension setup
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS child_chunks_embedding_hnsw_idx 
            ON child_chunks USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
        """))
    yield 

app = FastAPI(title="OmniDoc API", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(document.router) 

@app.get("/")
def health_check():
    return {"status": "OmniDoc API is running successfully with HNSW enabled."}