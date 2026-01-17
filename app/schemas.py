from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# --- AUTH ---
class AdminLogin(BaseModel):
    username: str
    password: str

# --- JOB SCHEMAS ---
class JobBase(BaseModel):
    title: str
    company: str
    location: str
    country: str
    job_type: str
    salary_range: str
    experience: str
    qualification: str
    description: str
    benefits: Optional[str] = "Free Food, Accommodation, Transportation + OT"
    project_duration: Optional[str] = "Minimum 03 Months"
    passport_req: Optional[str] = "ECNR Passport Required"
    interview_info: Optional[str] = "Online / Virtual Interview Shortly"

class JobCreate(JobBase):
    pass

class JobResponse(JobBase):
    id: int
    posted_on: datetime
    is_active: bool
    class Config:
        from_attributes = True

# --- CANDIDATE SCHEMAS ---
class CandidateBase(BaseModel):
    name: str
    skills: str
    experience_years: int
    whatsapp: str


class CandidateResponse(BaseModel):
    id: int
    name: str
    skills: str
    experience_years: int
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







