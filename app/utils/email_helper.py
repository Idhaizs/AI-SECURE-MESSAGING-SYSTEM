import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Ensure .env is explicitly loaded from project root directory regardless of working directory
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
env_path = os.path.join(BASE_DIR, '.env')
load_dotenv(env_path)

def get_smtp_config():
    # Reload env in case it was modified
    load_dotenv(env_path)
    return {
        'server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'port': int(os.getenv('SMTP_PORT', 587)),
        'user': os.getenv('SMTP_USER', '').strip(),
        'password': os.getenv('SMTP_PASSWORD', '').strip(),
        'sender': os.getenv('SENDER_EMAIL', os.getenv('SMTP_USER', '') or 'noreply@aisecuremessaging.com').strip(),
        'base_url': os.getenv('BASE_URL', 'https://aisecuremessaging.duckdns.org').strip()
    }

def send_approval_email(recipient_email, full_name, user_id_str):
    """
    Sends an approval email to the user with their assigned unique User ID.
    Returns (success: bool, message: str)
    """
    config = get_smtp_config()
    smtp_user = config['user']
    smtp_password = config['password']
    smtp_server = config['server']
    smtp_port = config['port']
    sender_email = config['sender']
    base_url = config['base_url']

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
                    <a href="{base_url}/login" class="btn">Login Now</a>
                </div>
            </div>
            <div class="footer">
                &copy; 2026 AI Secure Messaging System. Confidential & Secure Communication.
            </div>
        </div>
    </body>
    </html>
    """

    if smtp_user and smtp_password:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"AI Secure Messaging System <{sender_email}>"
        msg["To"] = recipient_email
        msg.attach(MIMEText(body_html, "html"))

        # Attempt 1: Port 587 (TLS)
        try:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(sender_email, recipient_email, msg.as_string())
            print(f"--> REAL Email successfully sent to {recipient_email} via SMTP (Port {smtp_port})!")
            return True, "Email sent successfully via SMTP Port 587"
        except Exception as e1:
            print(f"--> SMTP Port {smtp_port} failed: {e1}. Trying Port 465 (SSL) fallback...")

        # Attempt 2: Port 465 (SSL fallback)
        try:
            with smtplib.SMTP_SSL(smtp_server, 465, timeout=10) as server:
                server.login(smtp_user, smtp_password)
                server.sendmail(sender_email, recipient_email, msg.as_string())
            print(f"--> REAL Email successfully sent to {recipient_email} via SMTP SSL (Port 465)!")
            return True, "Email sent successfully via SMTP SSL Port 465"
        except Exception as e2:
            error_details = f"Port 587: {e1} | Port 465: {e2}"
            print(f"--> Error sending email via SMTP: {error_details}")
            return False, error_details

    mock_msg = f"SMTP_USER or SMTP_PASSWORD missing in .env (env_path: {env_path})"
    print(f"==================================================")
    print(f"[EMAIL] [MOCK EMAIL SENT TO: {recipient_email}]")
    print(f"Subject: {subject}")
    print(f"Assigned User ID: {user_id_str}")
    print(f"Reason: {mock_msg}")
    print(f"==================================================")
    return False, mock_msg

def send_rejection_email(recipient_email, full_name):
    """
    Sends a rejection email to the user if Admin rejects registration.
    """
    config = get_smtp_config()
    smtp_user = config['user']
    smtp_password = config['password']
    smtp_server = config['server']
    smtp_port = config['port']
    sender_email = config['sender']

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
    if smtp_user and smtp_password:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"AI Secure Messaging System <{sender_email}>"
        msg["To"] = recipient_email
        msg.attach(MIMEText(body_html, "html"))
        try:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(sender_email, recipient_email, msg.as_string())
            return True, "Rejection email sent"
        except Exception:
            try:
                with smtplib.SMTP_SSL(smtp_server, 465, timeout=10) as server:
                    server.login(smtp_user, smtp_password)
                    server.sendmail(sender_email, recipient_email, msg.as_string())
                return True, "Rejection email sent via SSL"
            except Exception as e:
                return False, str(e)

    return False, "SMTP_USER/SMTP_PASSWORD missing"

