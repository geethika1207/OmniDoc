# app/api/endpoints/chat.py
from fastapi import APIRouter
from starlette.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.service.embeddings import embed_single_chunk
from app.db.models import ChildChunk, ParentChunk


def retrieve_context(session_id: str, question: str, db: Session) -> str:
    question_vector = embed_single_chunk(question)
    
    relevant_children = (
        db.query(ChildChunk)
        .filter(ChildChunk.session_id == session_id)
        .order_by(ChildChunk.embedding.cosine_distance(question_vector))
        .limit(10)
        .all()
    )
        
    if not relevant_children:
        return ""
        

    unique_parent_ids = []
    for child in relevant_children:
        if child.parent_id not in unique_parent_ids:
            unique_parent_ids.append(child.parent_id)

            
    parent_chunks_from_db = (
        db.query(ParentChunk)
        .filter(
            ParentChunk.session_id == session_id,
            ParentChunk.id.in_(unique_parent_ids)
        )
        .all()
    )

    context_string = ""
    for parent in parent_chunks_from_db:
        context_string = context_string + parent.chunk_text + "\n\n"
        
    return context_string.strip()