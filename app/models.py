from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from .database import Base
import datetime

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    job_code = Column(String, unique=True)
    title = Column(String)
    company = Column(String)
    location = Column(String)
    experience = Column(String)
    qualification = Column(String)
    description = Column(Text)
    posted_on = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    skills = Column(String)
    experience_years = Column(Integer)
    video_url = Column(String) # Relative path to static/uploads/
    cv_url = Column(String)    # Relative path to static/uploads/
    whatsapp = Column(String)
    is_featured = Column(Boolean, default=False)

class Lead(Base):
    """Unified Lead table for Consultations and Recruitment"""
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)           # 'PAID_APPOINTMENT' or 'RECRUITMENT'
    email = Column(String, nullable=True)
    whatsapp = Column(String)
    
    # Consultancy Specific Fields
    service_type = Column(String, nullable=True)     # 'VISA' or 'JOB'
    country = Column(String, nullable=True)
    sub_type = Column(String, nullable=True)         # e.g., 'Work Visa' or 'Construction'
    appointment_date = Column(String, nullable=True) 
    
    # Payment Fields
    payment_method = Column(String, nullable=True)   # 'VISA', 'CRYPTO', 'MOMO', 'BANK'
    receipt_url = Column(String, nullable=True)      # Path to the payment proof image
    
    # Recruitment Specific Fields
    candidate_ids = Column(String, nullable=True)    # JSON string list of selected IDs
    
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)