import os
import logging
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from typing import Optional, List

# Setup logging to monitor email status in 'docker logs'
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connection configuration with fallback defaults to prevent startup crashes
conf = ConnectionConfig(
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", ""),
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", ""),
    MAIL_FROM = os.getenv("MAIL_FROM", "noreply@afroverseas.com"),
    MAIL_PORT = int(os.getenv("MAIL_PORT", 465)),
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.hostinger.com"),
    MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "Afroverseas Global"),
    MAIL_STARTTLS = False,
    MAIL_SSL_TLS = True,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

async def send_noreply_email(recipient: str, subject: str, body: str, attachment: Optional[str] = None):
    """
    Sends high-end professional HTML emails from noreply@afroverseas.com.
    Includes support for the Appointment Ticket QR Code attachments.
    """
    if not recipient:
        logger.warning("Attempted to send email but no recipient was provided.")
        return

    # Security check: Ensure credentials exist before attempting send
    if not conf.MAIL_USERNAME or not conf.MAIL_PASSWORD:
        logger.error("CRITICAL: Email credentials missing in environment (.env). Email not sent.")
        return

    try:
        # Prepare the message schema
        message = MessageSchema(
            subject=subject,
            recipients=[recipient], # Recipients must be in a list
            body=body,
            subtype="html",
            attachments=[attachment] if attachment else []
        )
        
        # Initialize FastMail and send
        fm = FastMail(conf)
        await fm.send_message(message)
        logger.info(f"Successfully sent professional email to: {recipient}")
        
    except Exception as e:
        # Prevent the backend from crashing if Hostinger SMTP is down or slow
        logger.error(f"SMTP Error while sending to {recipient}: {str(e)}")