import asyncio
import os
import aiosmtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

async def test_email():
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    
    print(f"Server: {smtp_server}:{smtp_port}")
    print(f"User: {smtp_user}")
    print(f"Password: {'*' * len(smtp_password) if smtp_password else 'NONE'}")
    
    if not smtp_password:
        print("ERROR: Password is missing in .env")
        return

    message = EmailMessage()
    message["From"] = smtp_user
    message["To"] = smtp_user
    message["Subject"] = "Test Email from Event Alerts"
    message.set_content("If you see this, SMTP is working!")

    try:
        print("Connecting...")
        await aiosmtplib.send(
            message,
            hostname=smtp_server,
            port=smtp_port,
            username=smtp_user,
            password=smtp_password,
            start_tls=True,
            validate_certs=False,
            timeout=30
        )
        print("SUCCESS: Email sent!")
    except Exception as e:
        print(f"FAILURE: {e}")

if __name__ == "__main__":
    asyncio.run(test_email())
