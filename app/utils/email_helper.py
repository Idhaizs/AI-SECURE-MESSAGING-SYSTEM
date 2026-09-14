import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
SENDER_EMAIL = os.getenv('SENDER_EMAIL', SMTP_USER or 'noreply@aisecuremessaging.com')

def send_approval_email(recipient_email, full_name, user_id_str):
    """
    Sends an approval email to the user with their assigned unique User ID.
    """
    subject = "🎉 Account Approved - AI Secure Messaging System"
    body_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; }}
            .container {{ max-width: 550px; background: #ffffff; border-radius: 12px; padding: 30px; margin: auto; box-shadow: 0 4px 15px rgba(0,0,0,0.08); border-top: 5px solid #1d4ed8; }}
            .header {{ text-align: center; padding-bottom: 20px; border-bottom: 1px solid #e2e8f0; }}
            .header h2 {{ color: #1e293b; margin: 5px 0; font-size: 22px; }}
            .content {{ padding: 20px 0; color: #334155; line-height: 1.6; }}
            .id-card {{ background-color: #f1f5f9; border: 2px dashed #94a3b8; border-radius: 8px; padding: 15px; text-align: center; margin: 20px 0; }}
            .id-card .label {{ font-size: 12px; text-transform: uppercase; color: #64748b; font-weight: bold; letter-spacing: 1px; }}
            .id-card .val {{ font-size: 26px; font-weight: 800; color: #1d4ed8; letter-spacing: 2px; margin-top: 5px; }}
            .btn {{ display: inline-block; background-color: #1d4ed8; color: #ffffff; text-decoration: none; padding: 12px 28px; border-radius: 6px; font-weight: bold; margin-top: 15px; text-align: center; }}
            .footer {{ text-align: center; margin-top: 25px; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0; padding-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>🛡️ AI Secure Messaging System</h2>
            </div>
            <div class="content">
                <p>Hello <strong>{full_name}</strong>,</p>
                <p>Great news! Your registration request has been reviewed and <strong>APPROVED</strong> by the System Administrator.</p>
                
                <div class="id-card">
                    <div class="label">Your Official System User ID</div>
                    <div class="val">{user_id_str}</div>
                </div>
                
                <p>Please keep this <strong>User ID</strong> safe. You will need to enter this ID when logging into the system.</p>
                
                <div style="text-align: center;">
                    <a href="http://localhost:5000/login" class="btn">Login Now</a>
                </div>
            </div>
            <div class="footer">
                &copy; 2026 AI Secure Messaging System. Confidential & Secure Communication.
            </div>
        </div>
    </body>
    </html>
    """

    if SMTP_USER and SMTP_PASSWORD:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = SENDER_EMAIL
            msg["To"] = recipient_email
            msg.attach(MIMEText(body_html, "html"))

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
            print(f"--> REAL Email successfully sent to {recipient_email} via SMTP!")
            return True
        except Exception as e:
            print(f"--> Error sending real email via SMTP: {e}")

    print(f"==================================================")
    print(f"[EMAIL] [MOCK EMAIL SENT TO: {recipient_email}]")
    print(f"Subject: {subject}")
    print(f"Assigned User ID: {user_id_str}")
    print(f"==================================================")
    return True

def send_rejection_email(recipient_email, full_name):
    """
    Sends a rejection email to the user if Admin rejects registration.
    """
    subject = "Registration Request Status - AI Secure Messaging System"
    body_html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
        <h2>🛡️ AI Secure Messaging System</h2>
        <p>Hello <strong>{full_name}</strong>,</p>
        <p>We regret to inform you that your registration request was <strong>REJECTED</strong> by the System Administrator.</p>
        <p>If you believe this is an error, please contact your administrator.</p>
    </body>
    </html>
    """
    if SMTP_USER and SMTP_PASSWORD:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = SENDER_EMAIL
            msg["To"] = recipient_email
            msg.attach(MIMEText(body_html, "html"))
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
            return True
        except Exception as e:
            print(f"--> Error sending email: {e}")

    print(f"[EMAIL] [MOCK REJECTION EMAIL SENT TO: {recipient_email}]")
    return True
