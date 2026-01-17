import os
import uuid
import qrcode
import aiofiles
import json
import io
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session

# Import local modules using the correct relative path (.. means go up to 'app' folder)
from .. import models, schemas, notify
from ..database import get_db

router = APIRouter(prefix="/api/admin", tags=["Admin Actions"])

# Constants
UPLOAD_DIR = "static/uploads"
QR_DIR = "static/qrcodes"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(QR_DIR, exist_ok=True)

# ==========================================
# 1. HELPERS (Optimized to prevent Linter/Complexity errors)
# ==========================================

def _boost_recruited_experts(db: Session, candidate_ids_json: str):
    """Sync helper to update social proof branding for candidates"""
    if not candidate_ids_json:
        return
    try:
        ids = json.loads(candidate_ids_json)
        db.query(models.Candidate).filter(models.Candidate.id.in_(ids)).update(
            {models.Candidate.booking_count: models.Candidate.booking_count + 1},
            synchronize_session=False
        )
    except Exception:
        pass

async def _generate_ticket_and_notify(lead: models.Lead, background_tasks: BackgroundTasks):
    """
    Asynchronous helper to generate QR and trigger email.
    Uses in-memory buffer to prevent thread blocking.
    """
    qr_fn = f"ticket_{lead.ref_number}.png"
    qr_path = os.path.join(QR_DIR, qr_fn)
    
    # 1. Generate QR Code in memory buffer (High-Performance)
    qr_img = qrcode.make(f"AFRO_VERIFIED:{lead.ref_number}")
    buf = io.BytesIO()
    qr_img.save(buf, format="PNG")
    qr_bytes = buf.getvalue()
    
    # 2. Write to disk using Async Aiofiles (No Error here anymore)
    async with aiofiles.open(qr_path, "wb") as f:
        await f.write(qr_bytes)
    
    # 3. Prepare Professional HTML Email
    if lead.email:
        email_body = f"""
        <html>
            <body style="font-family: 'Plus Jakarta Sans', sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: auto; border: 2px solid #0056A4; padding: 40px; border-radius: 30px;">
                    <h2 style="color: #0056A4; text-align: center; text-transform: uppercase;">Appointment Confirmed</h2>
                    <p>Dear Candidate,</p>
                    <p>Your payment for <b>Ref: {lead.ref_number}</b> has been manually verified by our finance team.</p>
                    <div style="background-color: #F8F9FB; padding: 30px; border-radius: 20px; margin: 25px 0; border: 1px solid #eee;">
                        <p style="margin: 5px 0;"><b>Service:</b> {lead.service_type}</p>
                        <p style="margin: 5px 0;"><b>Confirmed Date:</b> {lead.appointment_date}</p>
                        <p style="margin: 5px 0;"><b>Arrive At:</b> {lead.arrival_time}</p>
                        <p style="margin: 5px 0;"><b>Address:</b> {lead.address}</p>
                    </div>
                    <p style="text-align: center; font-weight: bold; color: #2D9C3C;">PRESENT THE ATTACHED QR CODE AT THE ENTRANCE.</p>
                </div>
            </body>
        </html>"""
        
        background_tasks.add_task(
            notify.send_noreply_email, 
            lead.email, 
            f"Official Appointment Ticket: {lead.ref_number}", 
            email_body, 
            attachment=qr_path
        )

# ==========================================
# 2. CONTENT MANAGEMENT (Jobs & Candidates)
# ==========================================

@router.post("/upload-job")
async def create_job(request: Request, db: Session = Depends(get_db)):
    """
    Bypasses positional argument limits by parsing form data directly.
    Matches all 14 fields in the Job Model.
    """
    form = await request.form()
    
    job_data = {
        "title": form.get("title"),
        "company": form.get("company"),
        "location": form.get("location"),
        "country": form.get("country"),
        "job_type": form.get("job_type"),
        "salary_range": form.get("salary_range"),
        "experience": form.get("experience"),
        "qualification": form.get("qualification"),
        "description": form.get("description"),
        "benefits": form.get("benefits", "Free Food, Accommodation, Transportation + OT"),
        "project_duration": form.get("project_duration", "Minimum 03 Months"),
        "passport_req": form.get("passport_req", "ECNR Passport Required"),
        "interview_info": form.get("interview_info", "Online / Virtual Interview Shortly"),
        "job_code": f"AFRO-{uuid.uuid4().hex[:5].upper()}"
    }

    db_job = models.Job(**job_data)
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return {"status": "success", "job_id": db_job.id}

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
    """Async candidate vetting to handle large files efficiently"""
    safe_name = name.replace(" ", "_").lower()
    uid = uuid.uuid4().hex[:6]
    
    cv_path = os.path.join(UPLOAD_DIR, f"cv_{safe_name}_{uid}.pdf")
    vid_path = os.path.join(UPLOAD_DIR, f"vid_{safe_name}_{uid}.mp4")

    # Write CV Async
    async with aiofiles.open(cv_path, "wb") as f:
        await f.write(await cv_file.read())
    
    # Write Video Async
    async with aiofiles.open(vid_path, "wb") as f:
        await f.write(await video_file.read())

    new_c = models.Candidate(
        name=name, skills=skills, experience_years=experience_years, 
        whatsapp=whatsapp, cv_url=f"/static/uploads/{os.path.basename(cv_path)}",
        video_url=f"/static/uploads/{os.path.basename(vid_path)}",
        booking_count=0
    )
    db.add(new_c)
    db.commit()
    return {"status": "success", "candidate_id": new_c.id}

# ==========================================
# 3. VERIFICATION & TICKETING
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
    Main Verification Entry Point. 
    Cognitive complexity is reduced by delegating tasks to helpers.
    """
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Entry record not found")

    if action == 'APPROVE':
        lead.status = "Approved"
        _boost_recruited_experts(db, lead.candidate_ids)
        await _generate_ticket_and_notify(lead, background_tasks)

    elif action == 'DENY':
        lead.status = "Rejected"
        if lead.email:
            background_tasks.add_task(
                notify.send_noreply_email, lead.email, 
                "Notice: Payment Verification", 
                "Your payment receipt could not be verified. Contact support via WhatsApp."
            )

    elif action == 'POSTPONE':
        if not new_date:
            raise HTTPException(status_code=400, detail="Date required for postponement.")
        lead.appointment_date = new_date
        lead.status = "Rescheduled"
        if lead.email:
            background_tasks.add_task(
                notify.send_noreply_email, lead.email, 
                "Appointment Update", 
                f"Your appointment {lead.ref_number} has been moved to {new_date}."
            )

    db.commit()
    return {"status": "success", "current_status": lead.status}