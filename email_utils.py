"""
Mind Link — Email Utility Module
Sends email notifications to patients when their appointment is approved or cancelled.
Uses Gmail SMTP via environment variables (no extra packages required).
"""

import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# ─── Config from environment ──────────────────────────────────────────────────
SMTP_HOST     = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT     = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER     = os.environ.get('SMTP_USER', '')        # e.g. yourname@gmail.com
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')    # Gmail App Password
FROM_NAME     = os.environ.get('FROM_NAME', 'Mind Link Psychiatry Clinic')
FROM_EMAIL    = os.environ.get('FROM_EMAIL', SMTP_USER)


# ─── HTML email templates ─────────────────────────────────────────────────────

def _approved_html(appointment: dict) -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Appointment Approved – Mind Link</title>
  <style>
    body {{ margin:0; padding:0; background:#f0f4f8; font-family:'Segoe UI',Arial,sans-serif; }}
    .wrapper {{ max-width:600px; margin:40px auto; background:#ffffff; border-radius:16px;
                overflow:hidden; box-shadow:0 8px 32px rgba(0,0,0,.10); }}
    .header {{ background:linear-gradient(135deg,#4f46e5 0%,#7c3aed 100%);
               padding:40px 32px; text-align:center; }}
    .header h1 {{ color:#fff; margin:0; font-size:26px; letter-spacing:-0.5px; }}
    .header p  {{ color:rgba(255,255,255,.85); margin:8px 0 0; font-size:14px; }}
    .badge {{ display:inline-block; background:#22c55e; color:#fff; border-radius:50px;
              padding:6px 20px; font-size:13px; font-weight:700; margin-top:16px;
              letter-spacing:0.5px; }}
    .body {{ padding:36px 32px; }}
    .body p {{ color:#374151; font-size:15px; line-height:1.7; margin:0 0 16px; }}
    .details {{ background:#f8fafc; border-radius:12px; padding:20px 24px; margin:24px 0;
                border-left:4px solid #4f46e5; }}
    .details table {{ width:100%; border-collapse:collapse; }}
    .details td {{ padding:7px 0; font-size:14px; color:#374151; vertical-align:top; }}
    .details td:first-child {{ font-weight:600; color:#4f46e5; width:42%; }}
    .cta {{ text-align:center; margin:28px 0; }}
    .footer {{ background:#f8fafc; padding:24px 32px; text-align:center;
               border-top:1px solid #e5e7eb; }}
    .footer p {{ color:#9ca3af; font-size:12px; margin:0; }}
  </style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>🧠 Mind Link</h1>
    <p>Psychiatry & Mental Wellness Clinic</p>
    <span class="badge">✅ Appointment Confirmed</span>
  </div>
  <div class="body">
    <p>Dear <strong>{appointment['name']}</strong>,</p>
    <p>Great news! Your appointment has been <strong>approved</strong>. We look forward to seeing you at the clinic.</p>

    <div class="details">
      <table>
        <tr><td>📅 Date</td><td>{appointment['preferred_date']}</td></tr>
        <tr><td>⏰ Time</td><td>{appointment['preferred_time']}</td></tr>
        <tr><td>🩺 Service</td><td>{appointment['service_type']}</td></tr>
        <tr><td>📞 Phone</td><td>{appointment['phone']}</td></tr>
      </table>
    </div>

    <p>Please arrive <strong>10 minutes early</strong> and bring any previous medical records if applicable.</p>
    <p>If you need to reschedule or have any questions, feel free to contact us at any time.</p>
    <p style="margin-top:24px;">Warm regards,<br/><strong>Mind Link Care Team</strong></p>
  </div>
  <div class="footer">
    <p>This is an automated notification from Mind Link Psychiatry &amp; Mental Wellness Clinic.<br/>
       Please do not reply directly to this email.</p>
  </div>
</div>
</body>
</html>
"""


def _cancelled_html(appointment: dict) -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Appointment Cancelled – Mind Link</title>
  <style>
    body {{ margin:0; padding:0; background:#f0f4f8; font-family:'Segoe UI',Arial,sans-serif; }}
    .wrapper {{ max-width:600px; margin:40px auto; background:#ffffff; border-radius:16px;
                overflow:hidden; box-shadow:0 8px 32px rgba(0,0,0,.10); }}
    .header {{ background:linear-gradient(135deg,#dc2626 0%,#9f1239 100%);
               padding:40px 32px; text-align:center; }}
    .header h1 {{ color:#fff; margin:0; font-size:26px; letter-spacing:-0.5px; }}
    .header p  {{ color:rgba(255,255,255,.85); margin:8px 0 0; font-size:14px; }}
    .badge {{ display:inline-block; background:#f59e0b; color:#fff; border-radius:50px;
              padding:6px 20px; font-size:13px; font-weight:700; margin-top:16px;
              letter-spacing:0.5px; }}
    .body {{ padding:36px 32px; }}
    .body p {{ color:#374151; font-size:15px; line-height:1.7; margin:0 0 16px; }}
    .details {{ background:#fff7f7; border-radius:12px; padding:20px 24px; margin:24px 0;
                border-left:4px solid #dc2626; }}
    .details table {{ width:100%; border-collapse:collapse; }}
    .details td {{ padding:7px 0; font-size:14px; color:#374151; vertical-align:top; }}
    .details td:first-child {{ font-weight:600; color:#dc2626; width:42%; }}
    .footer {{ background:#f8fafc; padding:24px 32px; text-align:center;
               border-top:1px solid #e5e7eb; }}
    .footer p {{ color:#9ca3af; font-size:12px; margin:0; }}
  </style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>🧠 Mind Link</h1>
    <p>Psychiatry & Mental Wellness Clinic</p>
    <span class="badge">❌ Appointment Cancelled</span>
  </div>
  <div class="body">
    <p>Dear <strong>{appointment['name']}</strong>,</p>
    <p>We regret to inform you that your appointment has been <strong>cancelled</strong>.</p>

    <div class="details">
      <table>
        <tr><td>📅 Date</td><td>{appointment['preferred_date']}</td></tr>
        <tr><td>⏰ Time</td><td>{appointment['preferred_time']}</td></tr>
        <tr><td>🩺 Service</td><td>{appointment['service_type']}</td></tr>
        <tr><td>📞 Phone</td><td>{appointment['phone']}</td></tr>
      </table>
    </div>

    <p>We apologise for any inconvenience. Please <strong>book a new appointment</strong> at your earliest convenience and our team will be happy to assist you.</p>
    <p>If you have any questions, do not hesitate to reach out to us.</p>
    <p style="margin-top:24px;">Warm regards,<br/><strong>Mind Link Care Team</strong></p>
  </div>
  <div class="footer">
    <p>This is an automated notification from Mind Link Psychiatry &amp; Mental Wellness Clinic.<br/>
       Please do not reply directly to this email.</p>
  </div>
</div>
</body>
</html>
"""


# ─── Core send function ───────────────────────────────────────────────────────

def send_appointment_email(appointment: dict, status: str) -> bool:
    """
    Send an HTML email to the patient when their appointment status changes.

    Args:
        appointment: dict with keys name, email, preferred_date, preferred_time,
                     service_type, phone.
        status:      'approved' | 'cancelled'

    Returns:
        True if the email was sent successfully, False otherwise.
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        print('[Email] SMTP credentials not configured — skipping email notification.')
        return False

    to_email = appointment.get('email', '')
    if not to_email:
        print('[Email] No patient email address — skipping.')
        return False

    if status == 'approved':
        subject  = '✅ Your Appointment is Confirmed – Mind Link'
        html_body = _approved_html(appointment)
    elif status == 'cancelled':
        subject  = '❌ Your Appointment has been Cancelled – Mind Link'
        html_body = _cancelled_html(appointment)
    else:
        return False

    # Build the MIME message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From']    = f'{FROM_NAME} <{FROM_EMAIL}>'
    msg['To']      = to_email

    # Plain-text fallback
    plain = (
        f"Dear {appointment['name']},\n\n"
        f"Your appointment status has been updated to: {status.upper()}.\n\n"
        f"Date    : {appointment['preferred_date']}\n"
        f"Time    : {appointment['preferred_time']}\n"
        f"Service : {appointment['service_type']}\n\n"
        f"Regards,\nMind Link Care Team"
    )
    msg.attach(MIMEText(plain, 'plain'))
    msg.attach(MIMEText(html_body, 'html'))

    try:
        context = ssl.create_default_context()
        # Try STARTTLS (port 587) first, fall back to SSL (port 465)
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(FROM_EMAIL, [to_email], msg.as_string())
        else:
            try:
                with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                    server.ehlo()
                    server.starttls(context=context)
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    server.sendmail(FROM_EMAIL, [to_email], msg.as_string())
            except (smtplib.SMTPException, OSError):
                # Fallback to SSL on port 465
                with smtplib.SMTP_SSL(SMTP_HOST, 465, context=context) as server:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    server.sendmail(FROM_EMAIL, [to_email], msg.as_string())
        print(f'[Email] Notification sent to {to_email} — status: {status}')
        return True
    except Exception as exc:
        print(f'[Email] Failed to send notification to {to_email}: {exc}')
        return False
