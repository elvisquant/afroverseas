from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from .database import Base
import datetime


class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    company = Column(String)
    location = Column(String)
    country = Column(String) 
    job_type = Column(String) 
    salary_range = Column(String)
    experience = Column(String)
    qualification = Column(String)
    description = Column(Text)
    project_duration = Column(String, default="Minimum 03 Months")
    passport_req = Column(String, default="ECNR Passport Required")
    benefits = Column(String, default="Free Food, Accommodation, Transportation + OT")
    interview_info = Column(String, default="Online / Virtual Interview Shortly")
    posted_on = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    skills = Column(String)
    experience_years = Column(Integer)
    video_url = Column(String)
    cv_url = Column(String)
    whatsapp = Column(String)
    is_featured = Column(Boolean, default=False)


class Lead(Base):
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    ref_number = Column(String, unique=True)
    type = Column(String)           # 'PAID_APPOINTMENT' or 'RECRUITMENT'
    email = Column(String, nullable=True)
    whatsapp = Column(String)

    # Wizard Data
    service_type = Column(String, nullable=True)     
    country = Column(String, nullable=True)
    sub_type = Column(String, nullable=True)  

    # Appointment Info
    appointment_date = Column(String, nullable=True) 
    arrival_time = Column(String, default="09:00 AM")
    address = Column(String, default="Afroverseas HQ, City Center, Bujumbura")

    # Payment & Manual Verification
    payment_method = Column(String, nullable=True)   
    receipt_url = Column(String, nullable=True)      
    status = Column(String, default="Pending Verification") 

    # Recruitment Cart Data
    candidate_ids = Column(String, nullable=True) # JSON list of IDs
    
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)









