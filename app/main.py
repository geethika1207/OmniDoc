from fastapi import FastAPI
from .db.database import engine, Base
from .routers import auth

#Create all database tables based on your models.py
Base.metadata.create_all(bind=engine)

#Initialize the FastAPI application
app = FastAPI()

#Include  routers to connect the endpoints
app.include_router(auth.router)

@app.get("/")
def health_check():
     return {"status": "OmniDoc API is running successfully."}