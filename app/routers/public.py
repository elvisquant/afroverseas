from fastapi import APIRouter, Depends,FastAPI
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
app = FastAPI()

router = APIRouter(prefix="/api", tags=["Public"])

@app.get("/jobs", response_model=List[schemas.JobResponse])
def get_public_jobs(db: Session = Depends(get_db)):
    return db.query(models.Job).filter(models.Job.is_active == True).all()

@app.get("/candidates", response_model=List[schemas.CandidateResponse])
def get_public_candidates(db: Session = Depends(get_db)):
    return db.query(models.Candidate).all()