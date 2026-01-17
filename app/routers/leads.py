import os
import uuid
import aiofiles # Optimized for Async file writing
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from .. import models, notify
from ..database import get_db

router = APIRouter(prefix="/api", tags=["User Leads"])

# Directory where payment receipts are saved
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/submit-lead")
async def handle_lead_submission(
    background_tasks: BackgroundTasks,
    type: str = Form(...),                  # 'PAID_APPOINTMENT' or 'RECRUITMENT'
    whatsapp: str = Form(...),              # Mandatory
    email: Optional[str] = Form(None),      # Optional
    service: Optional[str] = Form(None),    # 'VISA' or 'JOB'
    country: Optional[str] = Form(None),
    date: Optional[str] = Form(None),       # From the Calendar step
    payment_method: Optional[str] = Form(None),
    candidate_ids: Optional[str] = Form(None), 
    receipt: Optional[UploadFile] = File(None), 
    db: Session = Depends(get_db)
):
    """
    Handles the 5-step wizard and Recruitment Cart.
    Saves data and payment receipt proof asynchronously.
    """
    
    # 1. Generate Unique Reference Number
    ref = f"AFRO-{uuid.uuid4().hex[:6].upper()}"
    
    receipt_url = None

    # 2. Handle ASYNC File Upload (Non-blocking)
    if receipt:
        ext = os.path.splitext(receipt.filename)[1]
        filename = f"receipt_{ref}{ext}"
        save_path = os.path.join(UPLOAD_DIR, filename)
        
        # We use aiofiles to write the file without blocking the server thread
        async with aiofiles.open(save_path, "wb") as out_file:
            content = await receipt.read() # Read the file asynchronously
            await out_file.write(content)  # Write the file asynchronously
        
        receipt_url = f"/static/uploads/{filename}"

    # 3. Create Database Entry
    new_lead = models.Lead(
        ref_number=ref,
        type=type,
        whatsapp=whatsapp,
        email=email,
        service_type=service,
        country=country,
        appointment_date=date,
        payment_method=payment_method,
        receipt_url=receipt_url,
        candidate_ids=candidate_ids,
        status="Pending Verification",
        message=f"New {type} request for {service} to {country}."
    )

    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)

    # 4. Immediate Automated Confirmation (via noreply@afroverseas.com)
    if email:
        email_body = f"""
        <html>
            <body style="font-family: 'Plus Jakarta Sans', sans-serif; color: #333; line-height: 1.6;">
                <div style="max-width: 600px; margin: auto; border: 2px solid #0056A4; padding: 30px; border-radius: 25px; background-color: #ffffff;">
                    <h2 style="color: #0056A4; text-align: center;">RECEIPT LOGGED</h2>
                    <p>Dear Candidate,</p>
                    <p>Your payment receipt for <b>Reference: {ref}</b> has been securely uploaded to our system.</p>
                    
                    <div style="background-color: #F8F9FB; padding: 20px; border-radius: 15px; margin: 20px 0; border: 1px solid #eee;">
                        <p style="margin: 5px 0;"><b>Service Type:</b> {service}</p>
                        <p style="margin: 5px 0;"><b>Destination:</b> {country}</p>
                        <p style="margin: 5px 0;"><b>Requested Date:</b> {date}</p>
                        <p style="margin: 5px 0;"><b>Payment:</b> {payment_method}</p>
                    </div>
                    
                    <p style="font-weight: bold;">What happens next?</p>
                    <p>Our finance team is manually verifying your transaction. If valid, you will receive your <b>Entrance QR Code</b> and official Appointment Ticket via email and WhatsApp.</p>
                    
                    <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">
                    <p style="font-size: 11px; color: #999; text-align: center;">
                        This is an automated system notification from Afroverseas Global Network. Please do not reply directly to this email.
                    </p>
                </div>
            </body>
        </html>
        """
        background_tasks.add_task(
            notify.send_noreply_email, 
            email, 
            f"Afroverseas: Request Received [{ref}]", 
            email_body
        )

    return {
        "status": "success", 
        "reference_number": ref,
        "lead_id": new_lead.id
    }