from sqlalchemy.orm import Session
from app.service.embeddings import embed_single_chunk
from app.db.models import ChildChunk, ParentChunk


def retrieve_context(session_id: str, question: str, db: Session) -> str:
    # Embed user question
    question_vector = embed_single_chunk(question)
    
    # Searching top 10 child chunks by Cosine Distance
    relevant_children = (
        db.query(ChildChunk)
        .filter(ChildChunk.session_id == session_id)
        .order_by(ChildChunk.embedding.cosine_distance(question_vector))
        .limit(10)
        .all()
    )
        
    if not relevant_children:
        return ""
        
    # Extract and deduplicate parent IDs preserving order
    unique_parent_ids = []
    for child in relevant_children:
        if child.parent_id not in unique_parent_ids:
            unique_parent_ids.append(child.parent_id)
            
    # Fetching full parent chunks
    parent_chunks_from_db = (
        db.query(ParentChunk)
        .filter(
            ParentChunk.session_id == session_id,
            ParentChunk.id.in_(unique_parent_ids)
        )
        .all()
    )
    
    # Restore original vector rank order
    
    parent_text_map = {}
    for parent in parent_chunks_from_db:
        parent_text_map[parent.id] = parent.chunk_text
        
    final_ordered_texts = []
    for parent_id in unique_parent_ids:
        if parent_id in parent_text_map:
            final_ordered_texts.append(parent_text_map[parent_id])
            
    #  Merge into a single context string

    final_context_string = ""
    for text in final_ordered_texts:
        final_context_string = final_context_string + text + "\n\n"
        
    return final_context_string.strip()
