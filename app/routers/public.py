from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api", tags=["Public"])

@router.get("/jobs", response_model=List[schemas.JobResponse])
def get_jobs(
    search: Optional[str] = None,
    country: Optional[str] = None,
    job_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Job).filter(models.Job.is_active == True)
    
    if search:
        query = query.filter(models.Job.title.ilike(f"%{search}%") | models.Job.company.ilike(f"%{search}%"))
    if country:
        query = query.filter(models.Job.country == country)
    if job_type:
        query = query.filter(models.Job.job_type == job_type)
        
    return query.order_by(models.Job.posted_on.desc()).all()

@router.get("/candidates", response_model=List[schemas.CandidateResponse])
def get_candidates(db: Session = Depends(get_db)):
    # Order by booking count to show most popular experts first
    return db.query(models.Candidate).order_by(models.Candidate.booking_count.desc()).all()