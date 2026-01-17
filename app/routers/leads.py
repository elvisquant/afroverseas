import os
import shutil
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api", tags=["Leads"])

# Directory where receipts and CVs will be stored
UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/submit-lead")
async def handle_lead_submission(
    type: str = Form(...),                  # 'PAID_APPOINTMENT' or 'RECRUITMENT'
    whatsapp: str = Form(...),              # Mandatory
    email: Optional[str] = Form(None),      # Optional
    service: Optional[str] = Form(None),    # 'VISA' or 'JOB'
    country: Optional[str] = Form(None),
    date: Optional[str] = Form(None),       # From the Calendar
    payment_method: Optional[str] = Form(None),
    candidate_ids: Optional[str] = Form(None), # JSON string for recruitment
    receipt: Optional[UploadFile] = File(None), # The receipt image
    db: Session = Depends(get_db)
):
    """
    Handles the 5-step wizard and Recruitment Cart.
    Saves data and payment receipt proof.
    """
    
    receipt_path = None

    # 1. Handle File Upload if it exists (Receipt)
    if receipt:
        # Create a unique filename to prevent overwriting
        ext = os.path.splitext(receipt.filename)[1]
        unique_filename = f"receipt_{whatsapp}_{uuid.uuid4().hex}{ext}"
        save_to = os.path.join(UPLOAD_DIR, unique_filename)
        
        with open(save_to, "wb") as buffer:
            shutil.copyfileobj(receipt.file, buffer)
        
        receipt_path = f"/static/uploads/{unique_filename}"

    # 2. Create Database Entry
    new_lead = models.Lead(
        type=type,
        whatsapp=whatsapp,
        email=email,
        service_type=service,
        country=country,
        appointment_date=date,
        payment_method=payment_method,
        receipt_url=receipt_path,
        candidate_ids=candidate_ids,
        message=f"Request from {whatsapp} for {service} to {country}"
    )

    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)

    # 3. NOTIFICATION LOGIC (Placeholder)
    # This is where you trigger the email/WhatsApp to yourself.
    # We will build the actual email sender in the next step.
    print(f"NEW LEAD ALERT: {new_lead.type} from {new_lead.whatsapp}")

    return {
        "status": "success", 
        "message": "We have received your payment and request.",
        "lead_id": new_lead.id
    }