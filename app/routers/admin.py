import os
import uuid
import qrcode
import aiofiles  # Optimized for Async
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

# Local imports
from .. import models, schemas, notify
from ..database import get_db

router = APIRouter(prefix="/api/admin", tags=["Admin Actions"])

# Ensure directories exist
UPLOAD_DIR = "static/uploads"
QR_DIR = "static/qrcodes"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(QR_DIR, exist_ok=True)

# ==========================================
# 1. THE JOB FORM BUNDLE (Solves the Parameter Error)
# ==========================================
class JobForm:
    """
    This class collects all 14 fields from your model.
    By using this, the create_job function only has 2 parameters, 
    fixing your '13 authorized' error permanently.
    """
    def __init__(
        self,
        title: str = Form(...),
        company: str = Form(...),
        location: str = Form(...),
        country: str = Form(...),
        job_type: str = Form(...),
        salary_range: str = Form(...),
        experience: str = Form(...),
        qualification: str = Form(...),
        description: str = Form(...),
        project_duration: str = Form("Minimum 03 Months"),
        passport_req: str = Form("ECNR Passport Required"),
        benefits: str = Form("Free Food, Accommodation, Transportation + OT"),
        interview_info: str = Form("Online / Virtual Interview Shortly"),
    ):
        self.data = {
            "title": title, "company": company,
            "location": location, "country": country, "job_type": job_type,
            "salary_range": salary_range, "experience": experience,
            "qualification": qualification, "description": description,
            "project_duration": project_duration, "passport_req": passport_req,
            "benefits": benefits, "interview_info": interview_info
        }

# ==========================================
# 2. CONTENT MANAGEMENT ENDPOINTS
# ==========================================

@router.post("/upload-job")
def create_job(form: JobForm = Depends(), db: Session = Depends(get_db)):
    """Admin posts a new job vacancy live using the bundled form data"""
    db_job = models.Job(**form.data)
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return {"status": "success", "message": "Job published live", "job_id": db_job.id}

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
    """Vette a candidate with Interview Video and CV PDF asynchronously"""
    safe_name = name.replace(" ", "_").lower()
    unique_id = uuid.uuid4().hex[:6]
    
    # Save CV
    cv_fn = f"cv_{safe_name}_{unique_id}.pdf"
    async with aiofiles.open(os.path.join(UPLOAD_DIR, cv_fn), "wb") as f:
        await f.write(await cv_file.read())

    # Save Video
    vid_fn = f"vid_{safe_name}_{unique_id}.mp4"
    async with aiofiles.open(os.path.join(UPLOAD_DIR, vid_fn), "wb") as f:
        await f.write(await video_file.read())

    new_candidate = models.Candidate(
        name=name, skills=skills, experience_years=experience_years, whatsapp=whatsapp,
        cv_url=f"/static/uploads/{cv_fn}", video_url=f"/static/uploads/{vid_fn}"
    )
    db.add(new_candidate)
    db.commit()
    return {"status": "success", "candidate_id": new_candidate.id}


# ==========================================
# 3. VERIFICATION & TICKETING SYSTEM
# ==========================================

@router.put("/verify-lead/{lead_id}")
async def verify_lead(
    lead_id: int, 
    action: str = Form(...), # 'APPROVE', 'DENY', 'POSTPONE'
    new_date: Optional[str] = Form(None), 
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Manual Verification Logic:
    - APPROVE: Generates unique QR Ticket and sends detailed HTML entry ticket.
    - DENY: Sends rejection notification due to payment issue.
    - POSTPONE: Reschedules the appointment date and notifies the user.
    """
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Record not found")

    if action == 'APPROVE':
        lead.status = "Approved"
        # 1. Generate QR Code
        qr_fn = f"ticket_{lead.ref_number}.png"
        qr_path = os.path.join(QR_DIR, qr_fn)
        qr = qrcode.make(f"AFROVERSEAS_VALID:{lead.ref_number}")
        qr.save(qr_path)
        
        # 2. Send Ticket Email
        if lead.email:
            email_body = f"""
            <html>
                <body style="font-family: sans-serif; line-height: 1.5; color: #333;">
                    <div style="max-width: 600px; margin: auto; border: 2px solid #0056A4; padding: 40px; border-radius: 30px;">
                        <h2 style="color: #0056A4; text-align: center;">APPOINTMENT CONFIRMED</h2>
                        <p>Your payment for <b>Ref: {lead.ref_number}</b> has been manually verified.</p>
                        <div style="background-color: #f4f7fa; padding: 25px; border-radius: 20px; margin: 25px 0;">
                            <p><b>Service:</b> {lead.service_type} Assistance</p>
                            <p><b>Confirmed Date:</b> {lead.appointment_date}</p>
                            <p><b>Arrive At:</b> {lead.arrival_time}</p>
                            <p><b>Location:</b> {lead.address}</p>
                        </div>
                        <p style="text-align: center; font-weight: bold; color: #2D9C3C;">PRESENT ATTACHED QR CODE AT ENTRANCE.</p>
                    </div>
                </body>
            </html>
            """
            background_tasks.add_task(notify.send_noreply_email, lead.email, f"Entry Ticket: {lead.ref_number}", email_body, attachment=qr_path)

    elif action == 'DENY':
        lead.status = "Rejected"
        if lead.email:
            deny_body = "Your payment receipt could not be verified. Please contact support on WhatsApp."
            background_tasks.add_task(notify.send_noreply_email, lead.email, "Verification Failed", deny_body)

    elif action == 'POSTPONE':
        if not new_date: raise HTTPException(status_code=400, detail="New date required")
        lead.appointment_date = new_date
        lead.status = "Rescheduled"
        if lead.email:
            background_tasks.add_task(notify.send_noreply_email, lead.email, "Notice: Schedule Update", f"Appointment moved to {new_date}")

    db.commit()
    return {"status": "success", "new_status": lead.status}