import os
import shutil
import httpx
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

# Import your local files
import models
import schemas
from database import engine, SessionLocal

# --- DATABASE INITIALIZATION ---
# This creates your tables in Postgres automatically
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Global Recruit High-End API")

# --- CORS CONFIGURATION ---
# Allows your Frontend to talk to this Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- STATIC FILES MOUNTING ---
# Crucial: This makes your uploaded videos and CVs accessible to the browser
# Example: http://localhost:8000/static/uploads/video.mp4
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- DATABASE DEPENDENCY ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- GOOGLE AUTH HELPER ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "YOUR_CLIENT_ID_HERE")

async def verify_google_token(token: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={token}")
        if resp.status_code != 200:
            return None
        return resp.json()


# ==========================================
# 1. PUBLIC ENDPOINTS (No Account Needed)
# ==========================================

@app.get("/api/jobs")
def get_jobs(db: Session = Depends(get_db)):
    """Fetch all active jobs for the mobile app list"""
    return db.query(models.Job).filter(models.Job.is_active == True).order_by(models.Job.posted_on.desc()).all()

@app.get("/api/candidates")
def get_candidates(db: Session = Depends(get_db)):
    """Fetch vetted candidates with video interview links"""
    return db.query(models.Candidate).all()

@app.post("/api/submit-lead")
async def handle_lead(payload: dict, db: Session = Depends(get_db)):
    """
    Captures Appointments or Recruitment orders.
    Handles standard Email/WhatsApp or Google Verified Email.
    """
    email = payload.get("email")
    
    # If Google One-Tap was used
    if payload.get("google_token"):
        user_info = await verify_google_token(payload.get("google_token"))
        if user_info:
            email = user_info.get("email")

    new_lead = models.Lead(
        type=payload.get("type"), # 'APPOINTMENT' or 'RECRUITMENT'
        email=email,
        whatsapp=payload.get("whatsapp"),
        candidate_ids=",".join(map(str, payload.get("candidate_ids", []))),
        message=payload.get("message", "New request from platform")
    )
    
    db.add(new_lead)
    db.commit()

    # NOTE: Add your logic here to send a WhatsApp notification to YOUR phone
    return {"status": "success", "message": "Lead captured successfully"}


# ==========================================
# 2. ADMIN ENDPOINTS (Only for System Admin)
# ==========================================

@app.post("/api/admin/upload-job")
def create_job(job: schemas.JobCreate, db: Session = Depends(get_db)):
    """Admin posts a new job listing"""
    db_job = models.Job(**job.dict())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

@app.post("/api/admin/upload-candidate")
async def create_candidate(
    name: str = Form(...),
    skills: str = Form(...),
    experience_years: int = Form(...),
    whatsapp: str = Form(...),
    cv_file: UploadFile = File(...),
    video_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    The main engine: Admin uploads the candidate with their 
    interview video and CV PDF.
    """
    # Create safe filenames
    safe_name = name.replace(" ", "_").lower()
    
    # Save CV
    cv_filename = f"cv_{safe_name}_{cv_file.filename}"
    cv_path = os.path.join(UPLOAD_DIR, cv_filename)
    with open(cv_path, "wb") as buffer:
        shutil.copyfileobj(cv_file.file, buffer)

    # Save Video
    vid_filename = f"vid_{safe_name}_{video_file.filename}"
    vid_path = os.path.join(UPLOAD_DIR, vid_filename)
    with open(vid_path, "wb") as buffer:
        shutil.copyfileobj(video_file.file, buffer)

    # Save to Database (using paths relative to static)
    new_candidate = models.Candidate(
        name=name,
        skills=skills,
        experience_years=experience_years,
        whatsapp=whatsapp,
        cv_url=f"/static/uploads/{cv_filename}",
        video_url=f"/static/uploads/{vid_filename}"
    )
    
    db.add(new_candidate)
    db.commit()
    db.refresh(new_candidate)
    
    return {"status": "success", "candidate_id": new_candidate.id}

from fastapi.responses import FileResponse

@app.get("/")
async def read_index():
    # Since index.html is copied to /app/ in Docker
    return FileResponse('index.html')

# To run locally: uvicorn main:app --reload