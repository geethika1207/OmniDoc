from app.core.config import settings

# Map internal provider keys to the exact LiteLLM model strings
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

# Define strict routing thresholds to balance speed, cost, and rate limits

GROQ_LIMIT = 4000          
COHERE_LIMIT = 80000       
GEMINI_MAX_LIMIT = 1000000 

def build_messages(context: str, question: str):

    # Prompt that is given to a system
    system_prompt = "You are a highly precise analytical assistant. Answer using ONLY the provided context."    
    
    user_prompt = f"### Context:\n{context}\n\n### Question:\n{question}\n\n### Answer:"
    
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]