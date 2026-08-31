import asyncio
from sqlalchemy.orm import Session

from app.db.models import ParentChunk, ChildChunk

async def process_and_store_chunks(full_text, session_id, file_name, db: Session):
    parent_size = 3000
    child_size = 1000
    child_overlap = 200

    parent_start = 0
    total_length = len(full_text)

    # 1. Outer Loop: Parent Chunks
    while parent_start < total_length:
        parent_text = full_text[parent_start : parent_start + parent_size]

        # Let the database model auto-generate the ID
        db_parent = ParentChunk(
            session_id=session_id,
            file_name=file_name,
            chunk_text=parent_text
        )
        db.add(db_parent)
        
        # Push to the database temporarily so it creates and returns the ID
        db.flush()

        child_start = 0
        chunk_index = 0
        parent_length = len(parent_text)

        # 2. Inner Loop: Child Chunks
        while child_start < parent_length:
            child_text = parent_text[child_start : child_start + child_size]
            embedding = [0.0] * 384 

            # Link the child using the newly generated database ID (db_parent.id)
            db_child = ChildChunk(
                parent_id=db_parent.id,
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
    return f"Successfully chunked and saved {file_name} to the database."