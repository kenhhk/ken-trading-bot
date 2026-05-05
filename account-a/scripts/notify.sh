#!/usr/bin/env bash
# Notification wrapper — SMS + Email
# Usage: bash account-a/scripts/notify.sh "<message>" [--urgent]
# SMS sent via email-to-SMS carrier gateway (no extra service needed)
# Email sent via sendmail or curl SMTP

set -euo pipefail

NOTIFY_EMAIL="${NOTIFY_EMAIL:-kenhhk@gmail.com}"
NOTIFY_PHONE="${NOTIFY_PHONE:-+16462343838}"
FALLBACK_FILE="$(dirname "$0")/../memory/NOTIFICATIONS.md"

msg="${1:-}"
urgent="${2:-}"

if [[ -z "$msg" ]]; then
  echo "usage: notify.sh \"<message>\" [--urgent]" >&2
  exit 1
fi

stamp="$(date '+%Y-%m-%d %H:%M %Z')"

# ── Email-to-SMS carrier gateways ─────────────────────────────────────────
# Strips country code and formats for common US carriers
# The bot tries AT&T first (most common); update CARRIER_GATEWAY if needed
# Common gateways:
#   AT&T:     number@txt.att.net
#   T-Mobile: number@tmomail.net
#   Verizon:  number@vtext.com
#   Sprint:   number@messaging.sprintpcs.com

PHONE_DIGITS="${NOTIFY_PHONE//[^0-9]/}"
# Remove leading 1 if 11 digits
[[ ${#PHONE_DIGITS} -eq 11 && "${PHONE_DIGITS:0:1}" == "1" ]] && PHONE_DIGITS="${PHONE_DIGITS:1}"
SMS_GATEWAY="${PHONE_DIGITS}@tmomail.net"

# ── Try to send via Python smtplib (no external deps) ─────────────────────
send_notification() {
  python3 - <<PYEOF
import smtplib, os, sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

smtp_user = os.environ.get('SMTP_USER', '')
smtp_pass = os.environ.get('SMTP_PASS', '')
smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
smtp_port = int(os.environ.get('SMTP_PORT', '587'))

if not smtp_user or not smtp_pass:
    print("SMTP credentials not set — falling back to log file")
    sys.exit(1)

subject = "[TradingBot] $stamp"
body = """$msg

--
Ken's AI Trading Bot
Account: $(basename $(dirname $(dirname "$0")))
Time: $stamp
"""

# Send email
try:
    msg_email = MIMEMultipart()
    msg_email['From'] = smtp_user
    msg_email['To'] = '$NOTIFY_EMAIL'
    msg_email['Subject'] = subject
    msg_email.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg_email)
    print("Email sent")
except Exception as e:
    print(f"Email failed: {e}")

# Send SMS via gateway (short message only)
try:
    sms_short = body[:160]  # SMS limit
    msg_sms = MIMEText(sms_short, 'plain')
    msg_sms['From'] = smtp_user
    msg_sms['To'] = '$SMS_GATEWAY'
    msg_sms['Subject'] = ''

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg_sms)
    print("SMS sent")
except Exception as e:
    print(f"SMS failed: {e}")
PYEOF
}

# Try to send — fall back to log file if SMTP not configured
if ! send_notification 2>/dev/null; then
  # Fallback: append to local notifications log
  mkdir -p "$(dirname "$FALLBACK_FILE")"
  printf "\n---\n## %s\n%s\n" "$stamp" "$msg" >> "$FALLBACK_FILE"
  echo "[notify fallback] appended to NOTIFICATIONS.md"
fi

echo "$msg"
