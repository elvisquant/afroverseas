import os
import uuid
import qrcode
import aiofiles
import json
import io
import csv
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

# Local imports - navigating up to the 'app' folder
from .. import models, schemas, notify
from ..database import get_db

router = APIRouter(prefix="/api/admin", tags=["Admin Control Center"])

# Constants for storage
UPLOAD_DIR = "static/uploads"
QR_DIR = "static/qrcodes"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(QR_DIR, exist_ok=True)

# ==========================================
# 1. DASHBOARD ANALYTICS & REPORTS
# ==========================================

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    MERGED LOGIC: Returns all business metrics for the High-End Dashboard.
    Matches the counters in admin.html.
    """
    return {
        "total_leads": db.query(models.Lead).count(),
        "pending_leads": db.query(models.Lead).filter(models.Lead.status == "Pending Verification").count(),
        "approved_appointments": db.query(models.Lead).filter(models.Lead.status == "Approved").count(),
        "active_jobs": db.query(models.Job).filter(models.Job.is_active == True).count(),
        "experts_pool": db.query(models.Candidate).count()
    }

@router.get("/export-leads")
def export_leads_report(db: Session = Depends(get_db)):
    """Generates a professional CSV report for management analysis"""
    leads = db.query(models.Lead).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Reference", "WhatsApp", "Email", "Service", "Country", "Status", "Date"])
    
    for l in leads:
        writer.writerow([l.ref_number, l.whatsapp, l.email, l.service_type, l.country, l.status, l.created_at])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=Afroverseas_Operations_Report.csv"}
    )

# ==========================================
# 2. HELPER FUNCTIONS (Complexity Reduction)
# ==========================================

def _boost_recruited_experts(db: Session, candidate_ids_json: str):
    """Sync helper to update social proof branding for candidates"""
    if not candidate_ids_json: return
    try:
        ids = json.loads(candidate_ids_json)
        db.query(models.Candidate).filter(models.Candidate.id.in_(ids)).update(
            {models.Candidate.booking_count: models.Candidate.booking_count + 1},
            synchronize_session=False
        )
    except Exception: pass

async def _generate_ticket_and_notify(lead: models.Lead, background_tasks: BackgroundTasks):
    """Async helper to generate QR and trigger official ticket email"""
    qr_fn = f"ticket_{lead.ref_number}.png"
    qr_path = os.path.join(QR_DIR, qr_fn)
    
    # Generate QR in memory buffer
    qr_img = qrcode.make(f"AFRO_VERIFIED_TICKET:{lead.ref_number}")
    buf = io.BytesIO()
    qr_img.save(buf, format="PNG")
    qr_bytes = buf.getvalue()
    
    # Async write to disk
    async with aiofiles.open(qr_path, "wb") as f:
        await f.write(qr_bytes)
    
    if lead.email:
        email_body = f"""
        <html>
            <body style="font-family: sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: auto; border: 2px solid #0056A4; padding: 40px; border-radius: 30px; background: #fff;">
                    <h2 style="color: #0056A4; text-align: center; text-transform: uppercase;">Appointment Confirmed</h2>
                    <p>Dear Candidate, your payment for <b>Ref: {lead.ref_number}</b> has been manually verified.</p>
                    <div style="background-color: #F8F9FB; padding: 30px; border-radius: 20px; margin: 25px 0; border: 1px solid #eee;">
                        <p><b>Service:</b> {lead.service_type}<br><b>Date:</b> {lead.appointment_date}<br><b>Venue:</b> {lead.address}</p>
                    </div>
                    <p style="text-align: center; font-weight: bold; color: #2D9C3C;">PRESENT ATTACHED QR CODE AT ENTRANCE.</p>
                </div>
            </body>
        </html>"""
        background_tasks.add_task(notify.send_noreply_email, lead.email, f"Entry Ticket: {lead.ref_number}", email_body, attachment=qr_path)

# ==========================================
# 3. CONTENT & VERIFICATION ENDPOINTS
# ==========================================

@router.post("/upload-job")
async def create_job(request: Request, db: Session = Depends(get_db)):
    """Bypasses arg limits by using Request.form()"""
    form = await request.form()
    job_map = {
        "title": form.get("title"), "company": form.get("company"), "location": form.get("location"),
        "country": form.get("country"), "job_type": form.get("job_type"), "salary_range": form.get("salary_range"),
        "experience": form.get("experience"), "qualification": form.get("qualification"),
        "description": form.get("description"), "job_code": f"AFRO-{uuid.uuid4().hex[:5].upper()}",
        "project_duration": form.get("project_duration", "24 Months"),
        "passport_req": form.get("passport_req", "ECNR Required"),
        "benefits": form.get("benefits", "Accommodation + Food + Transport"),
        "interview_info": form.get("interview_info", "WhatsApp Video Call Shortly")
    }
    db_job = models.Job(**job_map)
    db.add(db_job)
    db.commit()
    return {"status": "success", "id": db_job.id}

@router.post("/upload-candidate")
async def create_candidate(
    name: str = Form(...), skills: str = Form(...), experience_years: int = Form(...),
    whatsapp: str = Form(...), cv_file: UploadFile = File(...), video_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    safe_name = name.replace(" ", "_").lower()
    uid = uuid.uuid4().hex[:6]
    cv_fn, vid_fn = f"cv_{safe_name}_{uid}.pdf", f"vid_{safe_name}_{uid}.mp4"
    
    async with aiofiles.open(os.path.join(UPLOAD_DIR, cv_fn), "wb") as f: await f.write(await cv_file.read())
    async with aiofiles.open(os.path.join(UPLOAD_DIR, vid_fn), "wb") as f: await f.write(await video_file.read())

    new_c = models.Candidate(
        name=name, skills=skills, experience_years=experience_years, whatsapp=whatsapp,
        cv_url=f"/static/uploads/{cv_fn}", video_url=f"/static/uploads/{vid_fn}", booking_count=0
    )
    db.add(new_c)
    db.commit()
    return {"status": "success"}

@router.put("/verify-lead/{lead_id}")
async def verify_lead(
    lead_id: int, action: str = Form(...), new_date: Optional[str] = Form(None), 
    background_tasks: BackgroundTasks = BackgroundTasks(), db: Session = Depends(get_db)
):
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead: raise HTTPException(status_code=404)

    if action == 'APPROVE':
        lead.status = "Approved"
        _boost_recruited_experts(db, lead.candidate_ids)
        await _generate_ticket_and_notify(lead, background_tasks)
    elif action == 'DENY':
        lead.status = "Rejected"
        if lead.email:
            background_tasks.add_task(notify.send_noreply_email, lead.email, "Verification Failed", "Receipt invalid.")
    elif action == 'POSTPONE':
        lead.appointment_date = new_date or lead.appointment_date
        lead.status = "Rescheduled"
        if lead.email:
            background_tasks.add_task(notify.send_noreply_email, lead.email, "Date Updated", f"Moved to {new_date}")

    db.commit()
    return {"status": "success", "new_status": lead.status}

@router.get("/leads/pending")
def get_pending_leads(db: Session = Depends(get_db)):
    """Fetch leads awaiting manual receipt verification"""
    return db.query(models.Lead).filter(models.Lead.status == "Pending Verification").all()