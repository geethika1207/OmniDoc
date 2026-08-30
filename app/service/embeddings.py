import cohere
from app.core.config import settings

co = cohere.Client(settings.COHERE_API_KEY)

def embed_single_chunk(text: str):
    response = co.embed(
        texts=[text],
        model="embed-english-light-v3.0", 
        input_type="search_document" 
    )
    
    return response.embeddings[0]