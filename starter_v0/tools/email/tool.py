from __future__ import annotations
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any
from tools._shared import err

def send_email(to: str, subject: str, body: str, confirmed: bool = False) -> dict[str, Any]:
    """Send an email to a recipient. Only executes when confirmed is True."""
    if not confirmed:
        return {
            "tool": "send_email",
            "status": "unconfirmed",
            "message": "Email was not sent because confirmed is False. Please ask the user for confirmation."
        }
        
    try:
        user = os.getenv("EMAIL_USER")
        password = os.getenv("EMAIL_PASS")
        
        # If credentials are not present, simulate sending (mock mode)
        if not user or not password:
            print(f"[MOCK EMAIL] To: {to} | Subject: {subject} | Body: {body}")
            return {
                "tool": "send_email",
                "status": "simulated",
                "to": to,
                "subject": subject,
                "message": "Email send simulated successfully (missing EMAIL_USER/EMAIL_PASS credentials)."
            }
            
        # Real SMTP sending for Gmail
        msg = MIMEMultipart()
        msg['From'] = user
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(user, password)
        server.sendmail(user, to, msg.as_string())
        server.quit()
        
        return {
            "tool": "send_email",
            "status": "sent",
            "to": to,
            "subject": subject,
            "message": "Email sent successfully via Gmail SMTP."
        }
    except Exception as exc:
        return err("send_email", exc)
