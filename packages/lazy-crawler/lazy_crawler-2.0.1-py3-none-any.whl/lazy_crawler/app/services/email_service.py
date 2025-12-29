import aiosmtplib
from email.message import EmailMessage
from lazy_crawler.app import config
import logging

logger = logging.getLogger(__name__)


async def send_contact_email(full_name: str, email: str, message: str):
    """
    Sends an email notification for a contact form submission.
    Uses official aiosmtplib.send() pattern with EmailMessage.
    """
    missing = [
        name
        for name, val in {
            "EMAIL_HOST": config.EMAIL_HOST,
            "EMAIL_HOST_USER": config.EMAIL_HOST_USER,
            "EMAIL_HOST_PASSWORD": config.EMAIL_HOST_PASSWORD,
            "EMAILS_FROM_EMAIL": config.EMAILS_FROM_EMAIL,
            "CONTACT_RECIPIENT_EMAIL": config.CONTACT_RECIPIENT_EMAIL,
        }.items()
        if not val
    ]

    if missing:
        logger.warning(
            f"Email configurations are missing: {', '.join(missing)}. Cannot send email."
        )
        return

    subject = f"New Contact Form Submission: {full_name}"
    formatted_message = message.replace("\n", "<br>")
    html_content = f"""
    <html>
        <body>
            <h2 style="color: #611f69;">New Contact Form Submission</h2>
            <p><strong>Full Name:</strong> {full_name}</p>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>Message:</strong></p>
            <div style="background: #f8f8f8; padding: 15px; border-radius: 5px; border: 1px solid #ddd;">
                {formatted_message}
            </div>
            <hr style="border: none; border-top: 1px solid #eee; margin-top: 20px;">
            <p style="font-size: 0.8rem; color: #888;">Sent from Crawlio Intelligence Notification System</p>
        </body>
    </html>
    """

    message_obj = EmailMessage()
    message_obj["Subject"] = subject
    message_obj["From"] = f"{config.EMAILS_FROM_NAME} <{config.EMAILS_FROM_EMAIL}>"
    message_obj["To"] = config.CONTACT_RECIPIENT_EMAIL
    message_obj.set_content(html_content, subtype="html")

    try:
        logger.debug(
            f"Sending email from {config.EMAILS_FROM_EMAIL} to {config.CONTACT_RECIPIENT_EMAIL}"
        )
        await aiosmtplib.send(
            message_obj,
            hostname=config.EMAIL_HOST,
            port=config.EMAIL_PORT,
            username=config.EMAIL_HOST_USER,
            password=config.EMAIL_HOST_PASSWORD,
            start_tls=True,
        )
        logger.info(f"Email sent successfully to {config.CONTACT_RECIPIENT_EMAIL}")
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
