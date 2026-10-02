"""
Mind Link — Email Utility Module
Sends transactional email notifications using the Resend SDK.

Outbound emails:
  1. New appointment notification   → Doctor / admin
  2. Appointment confirmed          → Patient
  3. Appointment cancelled/declined → Patient

Configuration (environment variables):
  RESEND_API_KEY  — Resend API key (required for email delivery)
  FROM_EMAIL      — Verified sender address in Resend
  DOCTOR_EMAIL    — Doctor/admin notification recipient

If RESEND_API_KEY is not set the module logs a warning and all send
functions return False without calling the Resend API.  This allows
local development without credentials.
"""

import os
import logging

# ─── Logger ──────────────────────────────────────────────────────────────────
logger = logging.getLogger('mindlink.email')
logger.setLevel(logging.INFO)
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter(
        '[Email] %(levelname)s  %(message)s'
    ))
    logger.addHandler(_handler)


# ─── Config from environment ─────────────────────────────────────────────────
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
FROM_EMAIL     = os.environ.get('FROM_EMAIL', '')
DOCTOR_EMAIL   = os.environ.get('DOCTOR_EMAIL', '')

# Startup diagnostics (never log the actual key value)
if not RESEND_API_KEY:
    logger.warning(
        'RESEND_API_KEY is not set — email sending is DISABLED. '
        'Set the environment variable to enable transactional emails.'
    )
else:
    logger.info('Resend API key detected — email sending is ENABLED.')

if not FROM_EMAIL:
    logger.warning(
        'FROM_EMAIL is not set — emails cannot be sent without a verified sender address.'
    )

if not DOCTOR_EMAIL:
    logger.warning(
        'DOCTOR_EMAIL is not set — new-appointment notifications to the doctor will be skipped.'
    )


# ─── Internal helpers ────────────────────────────────────────────────────────

def _is_email_configured() -> bool:
    """Return True only when Resend credentials are present."""
    return bool(RESEND_API_KEY and FROM_EMAIL)


def _send_email(*, to: str, subject: str, html: str, text: str, tag: str = '') -> bool:
    """Low-level wrapper around resend.Emails.send().

    Args:
        to:      Recipient email address.
        subject: Email subject line.
        html:    HTML body.
        text:    Plain-text fallback body.
        tag:     Short label for logging (e.g. 'approved', 'new-appointment').

    Returns:
        True on success, False on any failure.
    """
    if not _is_email_configured():
        logger.info(
            'Email skipped (credentials not configured) — tag=%s, recipient=<%s>',
            tag, to
        )
        return False

    if not to:
        logger.warning('Email skipped — no recipient address provided (tag=%s).', tag)
        return False

    try:
        import resend
        resend.api_key = RESEND_API_KEY

        params = {
            'from': FROM_EMAIL,
            'to': [to],
            'subject': subject,
            'html': html,
            'text': text,
        }

        result = resend.Emails.send(params)
        email_id = result.get('id', 'unknown') if isinstance(result, dict) else str(result)
        logger.info(
            'Email sent successfully — tag=%s, resend_id=%s',
            tag, email_id
        )
        return True

    except Exception as exc:
        # Log the error type and message but NEVER log API keys or
        # sensitive patient data.
        logger.error(
            'Email send failed — tag=%s, error=%s: %s',
            tag, type(exc).__name__, exc
        )
        return False


# ─── Service-type display helper ─────────────────────────────────────────────

def _format_service_type(raw: str) -> str:
    """Convert 'medication_management' → 'Medication Management'."""
    return raw.replace('_', ' ').title() if raw else 'General Consultation'


# ─── HTML email builders ─────────────────────────────────────────────────────

def _new_appointment_html(appointment: dict) -> str:
    """HTML for the doctor notification when a new appointment is requested."""
    name = appointment.get('name', 'N/A')
    date = appointment.get('preferred_date', 'N/A')
    time = appointment.get('preferred_time', 'N/A')
    phone = appointment.get('phone', 'N/A')
    service = _format_service_type(appointment.get('service_type', ''))

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>New Appointment Request – Mind Link</title>
  <style>
    body {{ margin:0; padding:0; background:#f0f4f8; font-family:'Segoe UI',Arial,sans-serif; }}
    .wrapper {{ max-width:600px; margin:40px auto; background:#ffffff; border-radius:16px;
                overflow:hidden; box-shadow:0 8px 32px rgba(0,0,0,.10); }}
    .header {{ background:linear-gradient(135deg,#2563eb 0%,#7c3aed 100%);
               padding:40px 32px; text-align:center; }}
    .header h1 {{ color:#fff; margin:0; font-size:26px; letter-spacing:-0.5px; }}
    .header p  {{ color:rgba(255,255,255,.85); margin:8px 0 0; font-size:14px; }}
    .badge {{ display:inline-block; background:#f59e0b; color:#fff; border-radius:50px;
              padding:6px 20px; font-size:13px; font-weight:700; margin-top:16px;
              letter-spacing:0.5px; }}
    .body {{ padding:36px 32px; }}
    .body p {{ color:#374151; font-size:15px; line-height:1.7; margin:0 0 16px; }}
    .details {{ background:#f8fafc; border-radius:12px; padding:20px 24px; margin:24px 0;
                border-left:4px solid #2563eb; }}
    .details table {{ width:100%; border-collapse:collapse; }}
    .details td {{ padding:7px 0; font-size:14px; color:#374151; vertical-align:top; }}
    .details td:first-child {{ font-weight:600; color:#2563eb; width:42%; }}
    .footer {{ background:#f8fafc; padding:24px 32px; text-align:center;
               border-top:1px solid #e5e7eb; }}
    .footer p {{ color:#9ca3af; font-size:12px; margin:0; }}
  </style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>🧠 Mind Link</h1>
    <p>Psychiatry &amp; Mental Wellness Clinic</p>
    <span class="badge">🔔 New Appointment Request</span>
  </div>
  <div class="body">
    <p>A new appointment request has been submitted and is awaiting your review.</p>

    <div class="details">
      <table>
        <tr><td>👤 Patient</td><td>{name}</td></tr>
        <tr><td>📅 Date</td><td>{date}</td></tr>
        <tr><td>⏰ Time</td><td>{time}</td></tr>
        <tr><td>🩺 Service</td><td>{service}</td></tr>
        <tr><td>📞 Phone</td><td>{phone}</td></tr>
      </table>
    </div>

    <p>Please log in to the <strong>Mind Link Admin Panel</strong> to accept or decline this request.</p>
    <p style="margin-top:24px;">— Mind Link System</p>
  </div>
  <div class="footer">
    <p>This is an automated notification from Mind Link Psychiatry &amp; Mental Wellness Clinic.<br/>
       Please do not reply directly to this email.</p>
  </div>
</div>
</body>
</html>"""


def _approved_html(appointment: dict) -> str:
    """HTML for patient confirmation when appointment is approved."""
    name = appointment.get('name', 'Patient')
    date = appointment.get('preferred_date', 'N/A')
    time = appointment.get('preferred_time', 'N/A')
    phone = appointment.get('phone', 'N/A')
    service = _format_service_type(appointment.get('service_type', ''))

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Appointment Confirmed – Mind Link</title>
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
    .footer {{ background:#f8fafc; padding:24px 32px; text-align:center;
               border-top:1px solid #e5e7eb; }}
    .footer p {{ color:#9ca3af; font-size:12px; margin:0; }}
  </style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>🧠 Mind Link</h1>
    <p>Psychiatry &amp; Mental Wellness Clinic</p>
    <span class="badge">✅ Appointment Confirmed</span>
  </div>
  <div class="body">
    <p>Dear <strong>{name}</strong>,</p>
    <p>Great news! Your appointment has been <strong>confirmed</strong>. We look forward to seeing you at the clinic.</p>

    <div class="details">
      <table>
        <tr><td>📅 Date</td><td>{date}</td></tr>
        <tr><td>⏰ Time</td><td>{time}</td></tr>
        <tr><td>🩺 Service</td><td>{service}</td></tr>
        <tr><td>📞 Phone</td><td>{phone}</td></tr>
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
</html>"""


def _cancelled_html(appointment: dict) -> str:
    """HTML for patient notification when appointment is cancelled/declined."""
    name = appointment.get('name', 'Patient')
    date = appointment.get('preferred_date', 'N/A')
    time = appointment.get('preferred_time', 'N/A')
    phone = appointment.get('phone', 'N/A')
    service = _format_service_type(appointment.get('service_type', ''))

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Appointment Update – Mind Link</title>
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
    <p>Psychiatry &amp; Mental Wellness Clinic</p>
    <span class="badge">📋 Appointment Update</span>
  </div>
  <div class="body">
    <p>Dear <strong>{name}</strong>,</p>
    <p>We regret to inform you that your appointment could not be confirmed at this time.</p>

    <div class="details">
      <table>
        <tr><td>📅 Requested Date</td><td>{date}</td></tr>
        <tr><td>⏰ Requested Time</td><td>{time}</td></tr>
        <tr><td>🩺 Service</td><td>{service}</td></tr>
        <tr><td>📞 Phone</td><td>{phone}</td></tr>
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
</html>"""


# ─── Plain-text builders ─────────────────────────────────────────────────────

def _new_appointment_text(appointment: dict) -> str:
    name = appointment.get('name', 'N/A')
    date = appointment.get('preferred_date', 'N/A')
    time = appointment.get('preferred_time', 'N/A')
    phone = appointment.get('phone', 'N/A')
    service = _format_service_type(appointment.get('service_type', ''))
    return (
        f"New Appointment Request — Mind Link\n"
        f"{'=' * 40}\n\n"
        f"A new appointment request has been submitted.\n\n"
        f"Patient : {name}\n"
        f"Date    : {date}\n"
        f"Time    : {time}\n"
        f"Service : {service}\n"
        f"Phone   : {phone}\n\n"
        f"Please log in to the Mind Link Admin Panel to accept or decline this request.\n\n"
        f"— Mind Link System"
    )


def _approved_text(appointment: dict) -> str:
    name = appointment.get('name', 'Patient')
    date = appointment.get('preferred_date', 'N/A')
    time = appointment.get('preferred_time', 'N/A')
    service = _format_service_type(appointment.get('service_type', ''))
    return (
        f"Dear {name},\n\n"
        f"Great news! Your appointment has been CONFIRMED.\n\n"
        f"Date    : {date}\n"
        f"Time    : {time}\n"
        f"Service : {service}\n\n"
        f"Please arrive 10 minutes early and bring any previous medical records if applicable.\n"
        f"If you need to reschedule or have any questions, feel free to contact us.\n\n"
        f"Warm regards,\n"
        f"Mind Link Care Team"
    )


def _cancelled_text(appointment: dict) -> str:
    name = appointment.get('name', 'Patient')
    date = appointment.get('preferred_date', 'N/A')
    time = appointment.get('preferred_time', 'N/A')
    service = _format_service_type(appointment.get('service_type', ''))
    return (
        f"Dear {name},\n\n"
        f"We regret to inform you that your appointment could not be confirmed.\n\n"
        f"Requested Date    : {date}\n"
        f"Requested Time    : {time}\n"
        f"Service           : {service}\n\n"
        f"We apologise for any inconvenience. Please book a new appointment at your\n"
        f"earliest convenience and our team will be happy to assist you.\n\n"
        f"Warm regards,\n"
        f"Mind Link Care Team"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API — called by app.py
# ═══════════════════════════════════════════════════════════════════════════════

def send_new_appointment_notification(appointment: dict) -> bool:
    """Notify the doctor/admin that a new appointment request was submitted.

    Called after a successful database insertion in the booking route.

    Args:
        appointment: dict with keys name, email, phone, preferred_date,
                     preferred_time, service_type.

    Returns:
        True if the email was sent, False otherwise.
    """
    if not DOCTOR_EMAIL:
        logger.info('Doctor notification skipped — DOCTOR_EMAIL is not configured.')
        return False

    return _send_email(
        to=DOCTOR_EMAIL,
        subject='New Appointment Request - Mind Link',
        html=_new_appointment_html(appointment),
        text=_new_appointment_text(appointment),
        tag='new-appointment',
    )


def send_appointment_accepted_email(appointment: dict) -> bool:
    """Send a confirmation email to the patient after approval.

    Args:
        appointment: dict with keys name, email, phone, preferred_date,
                     preferred_time, service_type.

    Returns:
        True if the email was sent, False otherwise.
    """
    to_email = appointment.get('email', '')
    return _send_email(
        to=to_email,
        subject='Appointment Confirmed - Mind Link',
        html=_approved_html(appointment),
        text=_approved_text(appointment),
        tag='approved',
    )


def send_appointment_declined_email(appointment: dict) -> bool:
    """Send a decline/cancellation email to the patient.

    Args:
        appointment: dict with keys name, email, phone, preferred_date,
                     preferred_time, service_type.

    Returns:
        True if the email was sent, False otherwise.
    """
    to_email = appointment.get('email', '')
    return _send_email(
        to=to_email,
        subject='Appointment Update - Mind Link',
        html=_cancelled_html(appointment),
        text=_cancelled_text(appointment),
        tag='cancelled',
    )


def send_appointment_email(appointment: dict, status: str) -> bool:
    """Backward-compatible dispatcher used by existing app.py call-sites.

    Routes to the appropriate Resend-based function depending on status.

    Args:
        appointment: appointment dict from the database.
        status:      'approved' | 'cancelled'

    Returns:
        True if the email was sent, False otherwise.
    """
    if status == 'approved':
        return send_appointment_accepted_email(appointment)
    elif status == 'cancelled':
        return send_appointment_declined_email(appointment)
    else:
        logger.warning('send_appointment_email called with unknown status=%s — skipping.', status)
        return False
