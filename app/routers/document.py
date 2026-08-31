from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import get_current_user
from app.service.pdf_processor import extract_pdf_content
from app.service.parent_child_chunks import process_and_store_chunks

from app.db.models import ParentChunk, ChildChunk 

router = APIRouter()

@router.post("/upload")
async def upload_documents(
    user_id: str = Depends(get_current_user),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")
        
    print(f"Starting document processing: received {len(files)} file(s) from user {user_id}.")

    # all_sample_texts list stores the frst few pages of all user uploaded pdfs to generate pop questions based on multiple user upload pdfs.

    all_sample_texts = []

    # It loops through evry pdf not files or pages in pdf
    for file in files:
        session_id = f"{file.filename}/{user_id}"
        
        # Extract text
        # file_sample is a starting few pages text that is used to generate pop up questions

        reader = PdfReader(file.file)
        full_text, file_sample = await extract_pdf_content(reader)
        all_sample_texts.append(file_sample)
        
        status_msg = await process_and_store_chunks(full_text, session_id, file.filename, db)
        
        #Query the database for just the very first parent and its children
        # it lets  verify it worked without returning the entire PDF and crashing the browser

        first_parent = db.query(ParentChunk).filter(ParentChunk.session_id == session_id).first()
        first_children = []
        if first_parent:
            first_children = db.query(ChildChunk).filter(ChildChunk.parent_id == first_parent.id).all()
        
        #Return a small part of the chunks to verifuy it works 
        return {
            "status": status_msg,
            "parent_chunk_preview": first_parent.chunk_text[:300] + "..." if first_parent else None,
            "child_chunks_created_for_this_parent": len(first_children),
            "first_child_preview": first_children[0].chunk_text[:150] + "..." if first_children else None,
            "first_child_embedding_sample": first_children[0].embedding[:3] if first_children else None # Just the first 3 vector numbers
        }