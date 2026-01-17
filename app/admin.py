import os
import uuid
import qrcode
import aiofiles # Optimized for Async
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

# Import local modules
from . import models, schemas, notify
from .database import get_db

router = APIRouter(prefix="/api/admin", tags=["Admin Actions"])

# Constants for directories
UPLOAD_DIR = "static/uploads"
QR_DIR = "static/qrcodes"

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(QR_DIR, exist_ok=True)

# ==========================================
# 1. CONTENT MANAGEMENT (Jobs & Candidates)
# ==========================================

@router.post("/upload-job")
def create_job(job: schemas.JobCreate, db: Session = Depends(get_db)):
    """Admin posts a new job vacancy live"""
    db_job = models.Job(**job.dict())
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
    """
    Vette a candidate with Interview Video and CV.
    Uses aiofiles for high-performance non-blocking uploads.
    """
    safe_name = name.replace(" ", "_").lower()
    unique_id = uuid.uuid4().hex[:6]
    
    # 1. Save CV PDF (Async)
    cv_filename = f"cv_{safe_name}_{unique_id}.pdf"
    cv_path = os.path.join(UPLOAD_DIR, cv_filename)
    async with aiofiles.open(cv_path, "wb") as out_file:
        content = await cv_file.read()
        await out_file.write(content)

    # 2. Save Interview Video (Async)
    video_filename = f"vid_{safe_name}_{unique_id}.mp4"
    video_path = os.path.join(UPLOAD_DIR, video_filename)
    async with aiofiles.open(video_path, "wb") as out_file:
        content = await video_file.read()
        await out_file.write(content)

    # 3. Save to Database
    new_candidate = models.Candidate(
        name=name,
        skills=skills,
        experience_years=experience_years,
        whatsapp=whatsapp,
        cv_url=f"/static/uploads/{cv_filename}",
        video_url=f"/static/uploads/{video_filename}"
    )
    db.add(new_candidate)
    db.commit()
    db.refresh(new_candidate)
    
    return {"status": "success", "candidate_id": new_candidate.id}


# ==========================================
# 2. TRANSACTION VERIFICATION & TICKETING
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
    Admin verification system:
    - APPROVE: Generates QR Ticket and sends entry details.
    - DENY: Informs user of payment failure.
    - POSTPONE: Reschedules and notifies user.
    """
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Appointment record not found")

    # --- CASE: APPROVE (Payment Confirmed) ---
    if action == 'APPROVE':
        lead.status = "Approved"
        
        # 1. Generate QR Code for Gate Verification
        qr_filename = f"ticket_{lead.ref_number}.png"
        qr_path = os.path.join(QR_DIR, qr_filename)
        qr_content = f"AFROVERSEAS_VERIFIED:{lead.ref_number}"
        qr = qrcode.make(qr_content)
        qr.save(qr_path)
        
        # 2. Prepare Detailed HTML Ticket Email
        if lead.email:
            email_body = f"""
            <html>
                <body style="font-family: 'Helvetica', sans-serif; color: #333;">
                    <div style="max-width: 600px; margin: auto; border: 2px solid #0056A4; padding: 30px; border-radius: 25px;">
                        <h2 style="color: #0056A4; text-align: center;">APPOINTMENT CONFIRMED</h2>
                        <p>Your payment for <b>Ref: {lead.ref_number}</b> has been verified.</p>
                        
                        <div style="background-color: #f4f7fa; padding: 25px; border-radius: 15px; margin: 25px 0;">
                            <p style="margin: 5px 0;"><b>Service:</b> {lead.service_type} Assistance</p>
                            <p style="margin: 5px 0;"><b>Confirmed Date:</b> {lead.appointment_date}</p>
                            <p style="margin: 5px 0;"><b>Arrival Time:</b> {lead.arrival_time}</p>
                            <p style="margin: 5px 0;"><b>Location:</b> {lead.address}</p>
                        </div>
                        
                        <p style="text-align: center; font-weight: bold; color: #2D9C3C;">
                            PRESENT THE ATTACHED QR CODE AT THE ENTRANCE.
                        </p>
                        <p style="font-size: 11px; color: #aaa; text-align: center; margin-top: 30px;">
                            Afroverseas Global Network - 2026 Official Appointment System.
                        </p>
                    </div>
                </body>
            </html>
            """
            # Send Email via noreply@afroverseas.com with attachment
            background_tasks.add_task(
                notify.send_noreply_email, 
                lead.email, 
                f"Your Entry Ticket: {lead.ref_number}", 
                email_body,
                attachment=qr_path
            )

    # --- CASE: DENY (Payment Rejected) ---
    elif action == 'DENY':
        lead.status = "Rejected"
        if lead.email:
            deny_body = f"""
            <h2 style="color: #d32f2f;">Verification Failed</h2>
            <p>Hello, the receipt provided for <b>{lead.ref_number}</b> could not be verified.</p>
            <p>Please contact our support team on WhatsApp immediately to rectify this.</p>
            """
            background_tasks.add_task(notify.send_noreply_email, lead.email, "Action Required: Payment Denied", deny_body)

    # --- CASE: POSTPONE (Reschedule) ---
    elif action == 'POSTPONE':
        if not new_date:
            raise HTTPException(status_code=400, detail="A new date must be specified.")
        
        old_date = lead.appointment_date
        lead.appointment_date = new_date
        lead.status = "Rescheduled"
        
        if lead.email:
            reschedule_body = f"""
            <h2>Appointment Rescheduled</h2>
            <p>Your appointment <b>{lead.ref_number}</b> has been moved.</p>
            <p><b>From:</b> {old_date} <br> <b>To:</b> {new_date}</p>
            <p>Your security QR code remains valid for the updated date.</p>
            """
            background_tasks.add_task(notify.send_noreply_email, lead.email, "Notice: Schedule Update", reschedule_body)

    db.commit()
    return {"status": "success", "new_status": lead.status}