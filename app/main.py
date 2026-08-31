from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text
from .db.database import engine, Base
from .routers import auth, document

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all base tables
    Base.metadata.create_all(bind=engine)
    
    # Configure Supabase Vector Database & HNSW Index
    with engine.begin() as conn:
        # Ensure pgvector is active in Supabase
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        
        # Build the HNSW index for lightning-fast cosine similarity searches
        # vector_cosine_ops tells pgvector to optimize for Cosine Distance
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS child_chunks_embedding_hnsw_idx 
            ON child_chunks USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
        """))
    
    yield 

# Initialize FastAPI with the lifespan manager
app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(document.router, prefix="/api") 

@app.get("/")
def health_check():
    return {"status": "OmniDoc API is running successfully with HNSW enabled."}