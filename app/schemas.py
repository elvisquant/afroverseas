from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# --- AUTH ---
class AdminLogin(BaseModel):
    username: str
    password: str

# --- JOB SCHEMAS ---
class JobBase(BaseModel):
    job_code: str
    title: str
    company: str
    location: str
    experience: str
    qualification: str
    description: str

class JobResponse(JobBase):
    id: int
    posted_on: datetime
    class Config:
        from_attributes = True

# --- CANDIDATE SCHEMAS ---
class CandidateBase(BaseModel):
    name: str
    skills: str
    experience_years: int
    whatsapp: str

class CandidateResponse(CandidateBase):
    id: int
    video_url: str
    cv_url: str
    class Config:
        from_attributes = True

# --- LEAD SCHEMAS ---
# Note: For multipart/form-data (with files), we usually define 
# parameters in the router, but these are useful for documentation.
class LeadResponse(BaseModel):
    id: int
    type: str
    whatsapp: str
    created_at: datetime
    class Config:
        from_attributes = True