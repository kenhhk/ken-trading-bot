#!/usr/bin/env python3
"""
TradingView Webhook Receiver
Validates incoming signals using TV_WEBHOOK_SECRET and writes to TV-SIGNALS.md

Deploy this on Railway (free tier) or any cloud Python host.
Set these environment variables on the host:
  TV_WEBHOOK_SECRET  — shared secret between TradingView alerts and this server
  GITHUB_TOKEN       — personal access token with repo write access
  GITHUB_REPO        — e.g. "kenhhk/ken-trading-bot"
  NOTIFY_EMAIL       — kenhhk@gmail.com
  NOTIFY_PHONE       — +16462343838

TradingView alert message format (paste into each alert):
{
  "secret": "YOUR_TV_WEBHOOK_SECRET",
  "ticker": "{{ticker}}",
  "signal": "SIGNAL_NAME",
  "indicator": "CTO_LINE" or "THT_FAIR_VALUE" or "THT_BX_TRENDER",
  "account": "A" or "B",
  "close": {{close}},
  "timeframe": "{{interval}}",
  "time": "{{time}}"
}
"""

import hashlib
import hmac
import json
import os
import re
import smtplib
from datetime import date, datetime, timedelta
from email.mime.text import MIMEText
from http.server import BaseHTTPRequestHandler, HTTPServer

# ── Config ─────────────────────────────────────────────────────────────────
TV_SECRET    = os.environ.get("TV_WEBHOOK_SECRET", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPO  = os.environ.get("GITHUB_REPO", "kenhhk/ken-trading-bot")
NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "kenhhk@gmail.com")
NOTIFY_PHONE = os.environ.get("NOTIFY_PHONE", "+16462343838")
SMTP_USER    = os.environ.get("SMTP_USER", "")
SMTP_PASS    = os.environ.get("SMTP_PASS", "")
PORT         = int(os.environ.get("PORT", "8080"))

# Signals that warrant immediate SMS notification
URGENT_SIGNALS = {"STRONG_BULL", "STRONG_BEAR", "BEARISH_FLIP",
                  "BULL_BAND", "BEAR_BAND", "BX_BULL_STRONG", "BX_BEAR"}

# ── GitHub file update ──────────────────────────────────────────────────────
def append_to_github_file(path: str, new_content: str) -> bool:
    """Append content to a file in the GitHub repo via API."""
    import urllib.request, base64

    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.github.v3+json",
    }

    # Get current file content and SHA
    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read())
        current_content = base64.b64decode(data["content"]).decode("utf-8")
        sha = data["sha"]
    except Exception as e:
        print(f"Failed to read {path}: {e}")
        return False

    updated_content = current_content + new_content
    encoded = base64.b64encode(updated_content.encode("utf-8")).decode("utf-8")

    body = json.dumps({
        "message": f"webhook signal received {datetime.utcnow().isoformat()[:16]}",
        "content": encoded,
        "sha": sha,
    }).encode()

    try:
        req = urllib.request.Request(api_url, data=body, headers=headers, method="PUT")
        with urllib.request.urlopen(req) as r:
            return r.status in (200, 201)
    except Exception as e:
        print(f"Failed to write {path}: {e}")
        return False


def format_signal_row(payload: dict) -> str:
    """Format a signal as a markdown table row for TV-SIGNALS.md."""
    now   = datetime.utcnow()
    today = now.strftime("%Y-%m-%d")
    time  = now.strftime("%H:%M UTC")
    return (
        f"| {today} | {time} | {payload.get('account','?')} "
        f"| {payload.get('ticker','?')} "
        f"| {payload.get('indicator','?')} "
        f"| {payload.get('signal','?')} "
        f"| {payload.get('close','?')} "
        f"| {payload.get('timeframe','?')} "
        f"| NEW |\n"
    )


def format_partial_signal_row(payload: dict) -> str:
    """Add to Active Partial Signals table for Account B."""
    today   = date.today().isoformat()
    expires = (date.today() + timedelta(days=30)).isoformat()
    return (
        f"| {today} | {payload.get('ticker','?')} "
        f"| {payload.get('indicator','?')} "
        f"| {payload.get('signal','?')} "
        f"| {expires} | Awaiting second indicator |\n"
    )


def send_sms_notification(message: str):
    """Send SMS via email-to-SMS gateway."""
    if not SMTP_USER or not SMTP_PASS:
        print("SMTP not configured — skipping SMS")
        return

    phone_digits = re.sub(r"[^0-9]", "", NOTIFY_PHONE)
    if len(phone_digits) == 11 and phone_digits[0] == "1":
        phone_digits = phone_digits[1:]
    sms_gateway = f"{phone_digits}@txt.att.net"

    try:
        msg = MIMEText(message[:160], "plain")
        msg["From"] = SMTP_USER
        msg["To"]   = sms_gateway
        msg["Subject"] = ""
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        print(f"SMS sent to {sms_gateway}")
    except Exception as e:
        print(f"SMS failed: {e}")


# ── HTTP Handler ────────────────────────────────────────────────────────────
class WebhookHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        """Health check endpoint."""
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Ken Trading Bot Webhook Receiver - OK")

    def do_POST(self):
        if self.path != "/webhook":
            self.send_response(404)
            self.end_headers()
            return

        # Read body
        length  = int(self.headers.get("Content-Length", 0))
        raw     = self.rfile.read(length)

        # Parse JSON
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid JSON")
            return

        # ── SECURITY: Validate secret ──────────────────────────────────────
        if not TV_SECRET:
            print("WARNING: TV_WEBHOOK_SECRET not set — rejecting all webhooks")
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"Webhook secret not configured")
            return

        received_secret = payload.get("secret", "")
        if not hmac.compare_digest(received_secret, TV_SECRET):
            print(f"REJECTED: Invalid webhook secret from {self.client_address[0]}")
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"Invalid secret")
            return

        # Remove secret from payload before logging
        payload.pop("secret", None)

        ticker  = payload.get("ticker", "UNKNOWN")
        signal  = payload.get("signal", "UNKNOWN")
        account = payload.get("account", "A")
        indicator = payload.get("indicator", "UNKNOWN")

        print(f"✅ Valid signal: {signal} for {ticker} (Acct {account}, {indicator})")

        # ── Write to TV-SIGNALS.md ─────────────────────────────────────────
        row = format_signal_row(payload)
        success = append_to_github_file("account-a/memory/TV-SIGNALS.md", row)

        # For Account B partial signals, also update Active Partial Signals table
        account_b_signals = {"BULL_BAND", "EARLY_BULL", "BEAR_BAND",
                             "BX_BULL_STRONG", "BX_BULL_EARLY", "BX_BEAR"}
        if account == "B" and signal in account_b_signals:
            partial_row = format_partial_signal_row(payload)
            # Note: in production, this would update the specific table section
            # For now, the signal-check routine handles combination detection
            print(f"Account B partial signal logged: {signal} for {ticker}")

        # ── SMS for urgent signals ─────────────────────────────────────────
        if signal in URGENT_SIGNALS:
            sms_msg = (
                f"TradingBot Alert! {signal} on {ticker} "
                f"(Acct {account}, {indicator}) "
                f"close=${payload.get('close','?')} "
                f"{payload.get('timeframe','?')}"
            )
            send_sms_notification(sms_msg)

        # ── Respond ────────────────────────────────────────────────────────
        if success:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "signal": signal, "ticker": ticker}).encode())
        else:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Failed to write to GitHub")

    def log_message(self, format, *args):
        print(f"[{datetime.utcnow().isoformat()[:19]}] {format % args}")


# ── Main ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not TV_SECRET:
        print("⚠️  WARNING: TV_WEBHOOK_SECRET not set — all webhooks will be rejected")
    if not GITHUB_TOKEN:
        print("⚠️  WARNING: GITHUB_TOKEN not set — signals cannot be written to repo")

    print(f"🚀 Webhook receiver starting on port {PORT}")
    server = HTTPServer(("0.0.0.0", PORT), WebhookHandler)
    server.serve_forever()
