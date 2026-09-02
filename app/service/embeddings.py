import cohere
from typing import List
from app.core.config import settings

co = cohere.Client(settings.COHERE_API_KEY)

def embed_batch_chunks(texts: List[str], input_type: str = "search_document") -> List[List[float]]:
    
    if not texts:
        return []

    all_embeddings = []
    batch_size = 96  # Cohere max batch size

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = co.embed(
            texts=batch,
            model="embed-english-light-v3.0",
            input_type=input_type
        )
        all_embeddings.extend(response.embeddings)

    return all_embeddings

def embed_single_chunk(text: str, input_type: str = "search_document") -> List[float]:

    embeddings = embed_batch_chunks([text], input_type=input_type)
    return embeddings[0]