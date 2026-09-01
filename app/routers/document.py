import uuid
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
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
        raise HTTPException(status_code=400, detail="No files uploaded.")
        
    print(f"Starting document processing: received {len(files)} file(s) from user {current_user.id}.")

    # Generating one session ID for the entire batch upload
    session_id = str(uuid.uuid4())
    
    # all_sample_texts contains the file samples that is the frst few pages of the pdf for all the user uploaded pdfs
    all_sample_texts = []

    for file in files:
        # Here every file shares the batch session_id.
        reader = PdfReader(file.file)
        
        # full_text is used for parent child chunking and file_sample is used to generate pop up questions
        full_text, file_sample = await extract_pdf_content(reader)
        all_sample_texts.append(file_sample)

        # It turns the full_text into multiple parent chunk and those parent chunk into multiple child chunks
        await process_and_store_chunks(
            full_text=full_text,
            session_id=session_id,
            file_name=file.filename,
            user_id=current_user.id,
            db=db
        )

    print(f"\nExtraction complete. Sending {len(all_sample_texts)} sample(s) ")

    # It generates pop up questions based on all the user uploaded pdfs
    suggested_questions = await generate_suggested_questions(all_sample_texts)

    print(f"Questions generated successfully: {suggested_questions}")

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
    # Awaiting the native async database search to quickly find relevant document chunks
    context_text = await retrieve_context(session_id, request.question, db)
    
    if not context_text:
        raise HTTPException(
            status_code=404, 
            detail="No relevant context found. Please ensure the document is uploaded."
        )
        
    # Passing the found text to the LLM and stream the response right back to the frontend
    generator = stream_completion(context_text, request.question)
    return StreamingResponse(generator, media_type="text/plain")