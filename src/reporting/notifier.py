import os
import aiosmtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

class Notifier:
    """Handles sending notifications via SMTP."""

    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.sender_email = os.getenv("SENDER_EMAIL", self.smtp_user)

    async def send_email(self, recipient: str, subject: str, html_content: str, attachment_path: str = None):
        """Sends an HTML email with an optional attachment."""
        if not self.smtp_user or not self.smtp_password:
            print("[Notifier] Error: SMTP credentials not found in environment.")
            return False

        message = EmailMessage()
        message["From"] = self.sender_email
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content("This is a multi-part message in MIME format.")
        message.add_alternative(html_content, subtype="html")

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                content = f.read()
                filename = os.path.basename(attachment_path)
                message.add_attachment(
                    content,
                    maintype="application",
                    subtype="octet-stream",
                    filename=filename
                )

        try:
            print(f"[Notifier] Sending email to {recipient}...")
            await aiosmtplib.send(
                message,
                hostname=self.smtp_server,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True
            )
            print("[Notifier] Email sent successfully.")
            return True
        except Exception as e:
            print(f"[Notifier] Failed to send email: {e}")
            return False
