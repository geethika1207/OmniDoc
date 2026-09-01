from fastapi import APIRouter
from starlette.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from app.service.embeddings import embed_single_chunk
from app.db.models import ChildChunk

router = APIRouter()

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
        
    return "" 