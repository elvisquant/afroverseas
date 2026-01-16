import os
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from database import get_db

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# UPLOAD DIRECTORY
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload-job")
def create_job(job: schemas.JobCreate, db: Session = Depends(get_db)):
    # Verify Admin Token here (we will add security later)
    db_job = models.Job(**job.dict())
    db.add(db_job)
    db.commit()
    return {"message": "Job posted successfully"}

@router.post("/upload-candidate")
async def create_candidate(
    name: str = Form(...),
    skills: str = Form(...),
    experience_years: int = Form(...),
    whatsapp: str = Form(...),
    cv_file: UploadFile = File(...),
    video_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. SAVE CV FILE
    cv_path = f"{UPLOAD_DIR}/cv_{name.replace(' ', '_')}_{cv_file.filename}"
    with open(cv_path, "wb") as buffer:
        shutil.copyfileobj(cv_file.file, buffer)

    # 2. SAVE VIDEO FILE
    video_path = f"{UPLOAD_DIR}/vid_{name.replace(' ', '_')}_{video_file.filename}"
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(video_file.file, buffer)

    # 3. SAVE TO DATABASE
    new_candidate = models.Candidate(
        name=name,
        skills=skills,
        experience_years=experience_years,
        whatsapp=whatsapp,
        cv_url=f"/{cv_path}",      # Path for the frontend to access
        video_url=f"/{video_path}" # Path for the frontend to access
    )
    db.add(new_candidate)
    db.commit()
    return {"message": "Candidate profile with video created successfully"}