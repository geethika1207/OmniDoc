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

    print(f"\nExtraction complete. Sending {len(all_sample_texts)} sample(s) ")
        
    suggested_questions = await generate_suggested_questions(all_sample_texts)
        
    print(f"Questions generated successfully: {suggested_questions}")

    return {
            "status": f"Successfully processed {len(files)} file(s).",
            "suggested_questions": suggested_questions
        }