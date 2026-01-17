import os
import logging
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from typing import Optional

# Setup logging to see errors in 'docker logs' if email fails
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

conf = ConnectionConfig(
    MAIL_USERNAME = os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD"),
    MAIL_FROM = os.getenv("MAIL_FROM"),
    MAIL_PORT = 465,
    MAIL_SERVER = "smtp.hostinger.com",
    MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "Afroverseas Group"),
    MAIL_STARTTLS = False,
    MAIL_SSL_TLS = True,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

async def send_noreply_email(recipient: str, subject: str, body: str, attachment: Optional[str] = None):
    """
    Sends professional HTML emails from noreply@afroverseas.com.
    Supports file attachments (like QR codes).
    """
    if not recipient:
        logger.warning("No recipient provided for email.")
        return
    
    try:
        message = MessageSchema(
            subject=subject,
            recipients=[recipient], # Must be a list
            body=body,
            subtype="html",
            attachments=[attachment] if attachment else []
        )
        
        fm = FastMail(conf)
        await fm.send_message(message)
        logger.info(f"Email successfully sent to {recipient}")
        
    except Exception as e:
        # This prevents the backend from crashing if the email server is slow
        logger.error(f"Failed to send email to {recipient}: {str(e)}")