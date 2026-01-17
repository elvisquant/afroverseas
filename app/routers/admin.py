import os
import uuid
import qrcode
import aiofiles # Optimized for Async
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session


from .. import models, notify
from ..database import get_db

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
def create_job(
    job_code: str = Form(...),
    title: str = Form(...),
    company: str = Form(...),
    location: str = Form(...),
    experience: str = Form(...),
    qualification: str = Form(...),
    description: str = Form(...),
    benefits: str = Form("Free Food, Accommodation, Transport + OT"),
    db: Session = Depends(get_db)
):
    """Allows admin to post complex job details"""
    db_job = models.Job(
        job_code=job_code, title=title, company=company, 
        location=location, experience=experience, 
        qualification=qualification, description=description,
        benefits=benefits
    )
    db.add(db_job)
    db.commit()
    return {"status": "success"}

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
    Vette a candidate with Interview Video and CV PDF.
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
    action: str = Form(...), # Expected: 'APPROVE', 'DENY', 'POSTPONE'
    new_date: Optional[str] = Form(None), 
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    High-End Manual Verification System:
    - APPROVE: Generates unique QR Ticket and sends detailed HTML entry ticket.
    - DENY: Sends rejection notification due to payment issue.
    - POSTPONE: Reschedules the appointment date and notifies the user.
    """
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Appointment record not found")

    # --- CASE: APPROVE (Payment Verified) ---
    if action == 'APPROVE':
        lead.status = "Approved"
        
        # 1. Generate QR Code for Gate Verification
        qr_filename = f"ticket_{lead.ref_number}.png"
        qr_path = os.path.join(QR_DIR, qr_filename)
        # Content used by scanning app at the office entrance
        qr_content = f"AFROVERSEAS_VERIFIED:{lead.ref_number}"
        qr = qrcode.make(qr_content)
        qr.save(qr_path)
        
        # 2. Prepare Detailed Professional HTML Ticket Email
        if lead.email:
            email_body = f"""
            <html>
                <body style="font-family: 'Helvetica', sans-serif; color: #333; line-height: 1.5;">
                    <div style="max-width: 600px; margin: auto; border: 2px solid #0056A4; padding: 40px; border-radius: 30px; background-color: white;">
                        <h2 style="color: #0056A4; text-align: center; margin-bottom: 30px;">OFFICIAL APPOINTMENT TICKET</h2>
                        <p>Dear Candidate,</p>
                        <p>We are pleased to inform you that your payment for <b>Reference: {lead.ref_number}</b> has been manually verified.</p>
                        
                        <div style="background-color: #f4f7fa; padding: 25px; border-radius: 20px; margin: 25px 0; border: 1px solid #e0e0e0;">
                            <p style="margin: 8px 0;"><b>Reference:</b> {lead.ref_number}</p>
                            <p style="margin: 8px 0;"><b>Service:</b> {lead.service_type} Assistance</p>
                            <p style="margin: 8px 0;"><b>Confirmed Date:</b> {lead.appointment_date}</p>
                            <p style="margin: 8px 0;"><b>Arrival Time:</b> {lead.arrival_time}</p>
                            <p style="margin: 8px 0;"><b>Venue:</b> {lead.address}</p>
                        </div>
                        
                        <div style="text-align: center; margin-top: 30px;">
                            <p style="font-weight: bold; color: #2D9C3C; font-size: 16px;">
                                PLEASE PRESENT THE ATTACHED QR CODE AT THE ENTRANCE.
                            </p>
                            <p style="font-size: 12px; color: #888;">
                                Ensure you arrive 15 minutes before your scheduled time.
                            </p>
                        </div>
                        
                        <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">
                        <p style="font-size: 10px; color: #aaa; text-align: center;">
                            Afroverseas Global Network © 2026. All rights reserved.
                        </p>
                    </div>
                </body>
            </html>
            """
            # Send Email via noreply@afroverseas.com with QR code attached
            background_tasks.add_task(
                notify.send_noreply_email, 
                lead.email, 
                f"Appointment Confirmed: {lead.ref_number}", 
                email_body,
                attachment=qr_path
            )

    # --- CASE: DENY (Payment Issue) ---
    elif action == 'DENY':
        lead.status = "Payment Rejected"
        if lead.email:
            deny_body = f"""
            <div style="font-family: sans-serif; padding: 20px; border: 1px solid #d32f2f; border-radius: 15px;">
                <h2 style="color: #d32f2f;">Verification Failed</h2>
                <p>Hello,</p>
                <p>Unfortunately, the receipt provided for <b>{lead.ref_number}</b> could not be verified by our finance team.</p>
                <p>This may be due to an incorrect amount or an invalid transaction proof. Please contact our support team on WhatsApp immediately to resolve this.</p>
            </div>
            """
            background_tasks.add_task(notify.send_noreply_email, lead.email, "Urgent: Payment Verification Failed", deny_body)

    # --- CASE: POSTPONE (Reschedule) ---
    elif action == 'POSTPONE':
        if not new_date:
            raise HTTPException(status_code=400, detail="A new date must be provided for rescheduling.")
        
        old_date = lead.appointment_date
        lead.appointment_date = new_date
        lead.status = "Rescheduled"
        
        if lead.email:
            reschedule_body = f"""
            <div style="font-family: sans-serif; padding: 20px; border: 1px solid #0056A4; border-radius: 15px;">
                <h2 style="color: #0056A4;">Appointment Rescheduled</h2>
                <p>Your appointment <b>{lead.ref_number}</b> has been moved by the consultant.</p>
                <p><b>Previous Date:</b> {old_date}</p>
                <p><b>New Confirmed Date:</b> {new_date}</p>
                <p>Your existing QR code and reference remain valid for the new date.</p>
            </div>
            """
            background_tasks.add_task(notify.send_noreply_email, lead.email, "Notice: Appointment Reschedule", reschedule_body)

    db.commit()
    return {"status": "success", "new_status": lead.status, "reference": lead.ref_number}