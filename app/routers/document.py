from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db.database import get_db
from ..core.security import get_current_user


router = APIRouter()

@router.post("/upload")
async def upload_documents(user_id =  Depends(get_current_user), files: List[UploadFile] = File(...), db: Session = Depends(get_db)):

    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    print(f"Starting document processing: received {len(files)}.")