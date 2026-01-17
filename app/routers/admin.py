from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
import shutil, os

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.post("/upload-candidate")
async def admin_upload_candidate(
    name: str = Form(...),
    skills: str = Form(...),
    experience_years: int = Form(...),
    whatsapp: str = Form(...),
    video_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Logic to save candidate video and create record
    video_filename = f"vid_{name.replace(' ', '_')}_{video_file.filename}"
    path = os.path.join("static/uploads", video_filename)
    
    with open(path, "wb") as buffer:
        shutil.copyfileobj(video_file.file, buffer)
        
    new_c = models.Candidate(
        name=name, skills=skills, 
        experience_years=experience_years, 
        whatsapp=whatsapp,
        video_url=f"/static/uploads/{video_filename}"
    )
    db.add(new_c)
    db.commit()
    return {"status": "success"}