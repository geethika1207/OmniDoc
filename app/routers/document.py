from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import get_current_user
from app.service.pdf_processor import extract_pdf_content

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

    for file in files:
        # Create your custom session ID
        session_id = f"{file.filename}/{user_id}"
        
        # Load the PDF into memory
        reader = PdfReader(file.file)
        
        full_text, file_sample = await extract_pdf_content(reader)
        
        return{"Full_text":full_text, "File_sample":file_sample}