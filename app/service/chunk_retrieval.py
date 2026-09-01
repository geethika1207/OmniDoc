from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.service.embeddings import embed_single_chunk
from app.db.models import ChildChunk, ParentChunk

async def retrieve_context(session_id: str, question: str, db: AsyncSession) -> str:
    question_vector = embed_single_chunk(question)
    
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
            
    # Fetching Parent Chunks asynchronously
    parent_stmt = (
        select(ParentChunk)
        .where(
            ParentChunk.session_id == session_id,
            ParentChunk.id.in_(unique_parent_ids)
        )
    )
    parent_result = await db.execute(parent_stmt)
    parent_chunks_from_db = parent_result.scalars().all()
    
    # Mapping and re-order parent texts
    parent_text_map = {parent.id: parent.chunk_text for parent in parent_chunks_from_db}
    final_ordered_texts = [
        parent_text_map[pid] for pid in unique_parent_ids if pid in parent_text_map
    ]
        
    return "\n\n".join(final_ordered_texts).strip()