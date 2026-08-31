from contextlib import asynccontextmanager
from fastapi import FastAPI

from .db.database import engine, Base
from .routers import auth, document

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic: Create all database tables based on your models.py
    Base.metadata.create_all(bind=engine)
    
    yield 

# Initialize the FastAPI application with the lifespan manager
app = FastAPI(lifespan=lifespan)

# Include routers to connect the endpoints
app.include_router(auth.router)
app.include_router(document.router) # Adjusts prefix if we use one

@app.get("/")
def health_check():
     return {"status": "OmniDoc API is running successfully."}