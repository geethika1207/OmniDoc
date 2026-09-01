from app.core.config import settings

MODELS = {
    "groq": "groq/llama-3.3-70b-versatile",
    "cohere": "cohere/command-r",
    "gemini": "gemini/gemini-2.0-flash"
}

API_KEYS = {
    "groq": settings.GROQ_API_KEY,
    "cohere": settings.COHERE_API_KEY,
    "gemini": settings.GEMINI_API_KEY
}

GROQ_LIMIT = 4000
COHERE_LIMIT = 80000
GEMINI_MAX_LIMIT = 1000000