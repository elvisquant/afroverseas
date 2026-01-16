from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    job_code = Column(String, unique=True) # e.g., JB00108415
    title = Column(String)
    company = Column(String)
    location = Column(String) # Saudi Arabia, etc.
    experience = Column(String) # 5-8 Years
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
    video_url = Column(String) # Link to GCP Storage video
    cv_url = Column(String)
    whatsapp = Column(String)
    is_featured = Column(Boolean, default=False)

class Lead(Base):
    """Captures both Appointments and Recruitment orders"""
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String) # 'APPOINTMENT' or 'RECRUITMENT'
    email = Column(String)
    whatsapp = Column(String)
    message = Column(Text)
    candidate_ids = Column(String) # JSON list of IDs they selected
    created_at = Column(DateTime, default=datetime.datetime.utcnow)