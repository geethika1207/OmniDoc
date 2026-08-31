from groq import AsyncGroq
from app.core.config import settings

# Initializing the async Groq client
client = AsyncGroq(api_key=settings.GROQ_API_KEY)

async def ask_groq(prompt: str) -> str:
    response = await client.chat.completions.create(
        model="openai/gpt-oss-120b", 
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=150
    )
    
    # Returning the text 
    return response.choices[0].message.content.strip()