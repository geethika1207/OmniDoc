from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.service.embeddings import embed_single_chunk
from app.db.models import ChildChunk, ParentChunk

async def retrieve_context(session_id: str, question: str, db: AsyncSession) -> str:
    # Use search_query input_type for search questions
    question_vector = embed_single_chunk(question, input_type="search_query")
    
    # Async pgvector Cosine Distance Query
    stmt = (
        select(ChildChunk)
        .where(ChildChunk.session_id == session_id)
        .order_by(ChildChunk.embedding.cosine_distance(question_vector))
        .limit(10)
    )
    result = await db.execute(stmt)
    relevant_children = result.scalars().all()
        
    if not relevant_children:
        return ""
        
    # Deduplicate parent IDs while preserving search ranking
    unique_parent_ids = []
    for child in relevant_children:
        if child.parent_id not in unique_parent_ids:
            unique_parent_ids.append(child.parent_id)
            
    # Fetch Parent Chunks asynchronously
    parent_stmt = (
        select(ParentChunk)
        .where(
            ParentChunk.session_id == session_id,
            ParentChunk.id.in_(unique_parent_ids)
        )
    )
    parent_result = await db.execute(parent_stmt)
    parent_chunks_from_db = parent_result.scalars().all()

    # Mapping and re-ordering parent texts to restore vector rank order
    parent_text_map = {}
    for parent in parent_chunks_from_db:
        parent_text_map[parent.id] = parent.chunk_text
        
    final_ordered_texts = []
    for parent_id in unique_parent_ids:
        if parent_id in parent_text_map:
            final_ordered_texts.append(parent_text_map[parent_id])
            
    # Merge everything into one string for the LLM
    final_context_string = ""
    for text in final_ordered_texts:
        final_context_string = final_context_string + text + "\n\n"
        
    return final_context_string.strip()