import uuid
import asyncio
from sqlalchemy.orm import Session

from app.db.models import ParentChunk, ChildChunk
from app.service.embeddings import embed_single_chunk

async def process_and_store_chunks(full_text, session_id, file_name, user_id, db: Session):
    parent_size = 3000
    child_size = 1000
    child_overlap = 200

    parent_start = 0
    total_length = len(full_text)

    # Outer Loop: Parent Chunks
    while parent_start < total_length:
        parent_text = full_text[parent_start : parent_start + parent_size]

        # Generates a unique String ID for the parent manually
        new_parent_id = str(uuid.uuid4())

        db_parent = ParentChunk(
            id=new_parent_id,
            session_id=session_id,
            user_id=user_id,    
            file_name=file_name,
            chunk_text=parent_text
        )
        db.add(db_parent)
        
        # db.flush() is no longer strictly needed here since ID is manually generated

        child_start = 0
        chunk_index = 0
        parent_length = len(parent_text)

        # Inner Loop: Child Chunks
        while child_start < parent_length:
            child_text = parent_text[child_start : child_start + child_size]
            
            embedding = embed_single_chunk(child_text)

            # Link the child using the manually generated parent ID
            db_child = ChildChunk(
                id=str(uuid.uuid4()),    
                parent_id=new_parent_id, 
                session_id=session_id,
                file_name=file_name,
                chunk_text=child_text,
                chunk_index=chunk_index,
                embedding=embedding
            )
            db.add(db_child)

            chunk_index = chunk_index + 1
            child_start = child_start + (child_size - child_overlap)

        parent_start = parent_start + parent_size
        await asyncio.sleep(0)

    db.commit()
   
    return f"Successfully chunked, embedded, and saved {file_name} to the database."