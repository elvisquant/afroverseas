from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# --- ADMIN AUTH ---
class AdminLogin(BaseModel):
    username: str
    password: str

# --- DATA SCHEMAS ---
class JobCreate(BaseModel):
    job_code: str
    title: str
    company: str
    location: str
    experience: str
    qualification: str
    description: str

class CandidateCreate(BaseModel):
    name: str
    skills: str
    experience_years: int
    whatsapp: str