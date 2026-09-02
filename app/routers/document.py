import uuid
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pypdf import PdfReader
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import User
from app.core.security import get_current_user
from app.service.pdf_processor import extract_pdf_content
from app.service.parent_child_chunks import process_and_store_chunks
from app.service.question_generator import generate_suggested_questions
from app.service.chunk_retrieval import retrieve_context
from app.service.llm_service import stream_completion
from app.schemas.document import ChatRequest

router = APIRouter()

@router.post("/upload")
async def upload_documents(
    current_user: User = Depends(get_current_user),
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db)
):
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files uploaded.")
        
    print(f"Starting document processing: received {len(files)} file(s) from user {current_user.id}.")

    session_id = str(uuid.uuid4())
    all_sample_texts = []

    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type for '{file.filename}'. Only PDF files are supported."
            )

        try:
            reader = PdfReader(file.file)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not read PDF '{file.filename}'. The file may be corrupt or empty."
            )
        
        full_text, file_sample = await extract_pdf_content(reader)
        
        if file_sample:
            all_sample_texts.append(file_sample)

        await process_and_store_chunks(
            full_text=full_text,
            session_id=session_id,
            file_name=file.filename,
            user_id=current_user.id,
            db=db
        )

    suggested_questions = await generate_suggested_questions(all_sample_texts)

    return {
        "session_id": session_id,
        "suggested_questions": suggested_questions
    }


@router.post("/chat/{session_id}")
async def chat_with_document(
    session_id: str,
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    context_text = await retrieve_context(session_id, request.question, db)
    
    if not context_text:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="No relevant context found. Please ensure the document is uploaded."
        )
        
    generator = stream_completion(context_text, request.question)
    return StreamingResponse(generator, media_type="text/plain")