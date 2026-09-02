import uuid
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import ParentChunk, ChildChunk
from app.service.embeddings import embed_batch_chunks

async def process_and_store_chunks(
    full_text: str,
    session_id: str,
    file_name: str,
    user_id: str,
    db: AsyncSession
):
    parent_size = 3000
    child_size = 1000
    child_overlap = 200

    parent_start = 0
    total_length = len(full_text)

    pending_children = []

    while parent_start < total_length:
        parent_text = full_text[parent_start : parent_start + parent_size]
        new_parent_id = str(uuid.uuid4())

        db_parent = ParentChunk(
            id=new_parent_id,
            session_id=session_id,
            user_id=user_id,
            file_name=file_name,
            chunk_text=parent_text
        )
        db.add(db_parent)

        child_start = 0
        chunk_index = 0
        parent_length = len(parent_text)

        while child_start < parent_length:
            child_text = parent_text[child_start : child_start + child_size]
            
            pending_children.append({
                "parent_id": new_parent_id,
                "text": child_text,
                "chunk_index": chunk_index
            })

            chunk_index += 1
            child_start += (child_size - child_overlap)

        parent_start += parent_size
        await asyncio.sleep(0)

    # Batch embed all child chunks in one request instead of one-by-one
    if pending_children:
        child_texts = [child["text"] for child in pending_children]
        embeddings = embed_batch_chunks(child_texts, input_type="search_document")

        for child_data, embedding in zip(pending_children, embeddings):
            db_child = ChildChunk(
                id=str(uuid.uuid4()),
                parent_id=child_data["parent_id"],
                session_id=session_id,
                file_name=file_name,
                chunk_text=child_data["text"],
                chunk_index=child_data["chunk_index"],
                embedding=embedding
            )
            db.add(db_child)

    await db.commit()
    
    return f"Successfully chunked, embedded, and saved {file_name} to the database."