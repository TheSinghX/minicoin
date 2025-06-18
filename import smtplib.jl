import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

load_dotenv()

email_address = os.getenv("SMTP_EMAIL")
email_password = os.getenv("SMTP_PASSWORD")

msg = EmailMessage()
msg.set_content("Test email from Flask OTP app")
msg["Subject"] = "Test OTP"
msg["From"] = email_address
msg["To"] = "yourpersonalemail@example.com"  # Replace with your real email

try:
    with smtplib.SMTP(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT"))) as smtp:
        smtp.starttls()
        smtp.login(email_address, email_password)
        smtp.send_message(msg)
        print("✅ Email sent successfully.")
except Exception as e:
    print("❌ Error sending email:", e)
