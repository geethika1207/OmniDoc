import uuid
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import get_current_user
from app.service.pdf_processor import extract_pdf_content
from app.service.parent_child_chunks import process_and_store_chunks
from app.service.question_generator import generate_suggested_questions

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

    # 1. Generating one session ID for the entire batch upload
    session_id = str(uuid.uuid4())
    
    all_sample_texts = []

    for file in files:
        # 2. We no longer generate a unique ID here. Every file shares the batch session_id.
        reader = PdfReader(file.file)
        full_text, file_sample = await extract_pdf_content(reader)
        all_sample_texts.append(file_sample)
        
        await process_and_store_chunks(full_text, session_id, file.filename, user_id, db)
        
    print(f"\nExtraction complete. Sending {len(all_sample_texts)} sample(s) ")
        
    suggested_questions = await generate_suggested_questions(all_sample_texts)
        
    print(f"Questions generated successfully: {suggested_questions}")

    return {
        "session_id": session_id,
        "suggested_questions": suggested_questions
    }