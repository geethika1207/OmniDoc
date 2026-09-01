from pydantic_settings import BaseSettings
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    DATABASE_USERNAME : str
    DATABASE_PASSWORD : str
    DATABASE_HOSTNAME : str
    DATABASE_PORT : str
    DATABASE_NAME : str
    ACCESS_EXPIRETIME_MINUTES : int
    SECRET_KEY : str
    ALGORITHM : str
    COHERE_API_KEY : str
    GROQ_API_KEY : str
    GEMINI_API_KEY : str 
    class Config:
        env_file = str(ROOT_DIR / ".env")

settings = Settings() 