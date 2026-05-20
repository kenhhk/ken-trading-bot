"""Email + SMS notifications. Matches Account A's notification style."""

import os
import re
import smtplib
from email.mime.text import MIMEText
from typing import Optional


SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "kenhhk@gmail.com")
NOTIFY_PHONE = os.environ.get("NOTIFY_PHONE", "+16462343838")


def send_email(subject: str, body: str, to: Optional[str] = None) -> bool:
    if not SMTP_USER or not SMTP_PASS:
        print(f"[notify] SMTP not configured; would have sent: {subject}")
        return False
    msg = MIMEText(body, "plain")
    msg["From"] = SMTP_USER
    msg["To"] = to or NOTIFY_EMAIL
    msg["Subject"] = subject
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as srv:
            srv.starttls()
            srv.login(SMTP_USER, SMTP_PASS)
            srv.send_message(msg)
        print(f"[notify] email sent: {subject}")
        return True
    except Exception as e:
        print(f"[notify] email FAILED: {e}")
        return False


def send_sms(message: str) -> bool:
    """Email-to-SMS gateway (AT&T). 160 char limit."""
    if not SMTP_USER or not SMTP_PASS:
        print(f"[notify] SMTP not configured; would have SMS'd: {message[:60]}")
        return False
    digits = re.sub(r"[^0-9]", "", NOTIFY_PHONE)
    if len(digits) == 11 and digits[0] == "1":
        digits = digits[1:]
    gateway = f"{digits}@tmomail.net"
    msg = MIMEText(message[:160], "plain")
    msg["From"] = SMTP_USER
    msg["To"] = gateway
    msg["Subject"] = ""
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as srv:
            srv.starttls()
            srv.login(SMTP_USER, SMTP_PASS)
            srv.send_message(msg)
        print(f"[notify] sms sent: {message[:40]}")
        return True
    except Exception as e:
        print(f"[notify] sms FAILED: {e}")
        return False


def alert(subject: str, body: str, sms: bool = False) -> None:
    """Send email; optionally SMS for urgent alerts."""
    send_email(f"Acct-B {subject}", body)
    if sms:
        send_sms(f"Acct-B {subject}: {body[:100]}")
