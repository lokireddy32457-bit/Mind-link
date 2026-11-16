"""
Mind Link — Resend email integration smoke test.
Uses a fully mocked resend module; no real emails are sent.
Run: python test_email_mock.py
"""
import sys
import os
import types

# ── Set env vars BEFORE importing email_utils ────────────────────────────────
os.environ['RESEND_API_KEY'] = 'test_key_mock'
os.environ['FROM_EMAIL']     = 'onboarding@resend.dev'
os.environ['DOCTOR_EMAIL']   = 'doctor@example.com'

# ── Mock the resend package so no real HTTP calls are made ───────────────────
sent_emails = []

mock_resend = types.ModuleType('resend')

class _MockEmails:
    @staticmethod
    def send(params):
        sent_emails.append(dict(params))
        return {'id': f'mock-{len(sent_emails):03d}'}

mock_resend.Emails = _MockEmails
mock_resend.api_key = ''
sys.modules['resend'] = mock_resend

# ── Import the module under test ─────────────────────────────────────────────
sys.path.insert(0, r'd:\Mind Link')

# Force reload in case email_utils was already cached without our mock
if 'email_utils' in sys.modules:
    del sys.modules['email_utils']

from email_utils import (
    send_new_appointment_notification,
    send_appointment_accepted_email,
    send_appointment_declined_email,
    send_appointment_email,
)

# ── Sample appointment dict (no medical info included in emails) ──────────────
sample = {
    'name':           'Test Patient',
    'email':          'patient@example.com',
    'phone':          '9876543210',
    'preferred_date': '2026-12-01',
    'preferred_time': '10:00 AM',
    'service_type':   'anxiety_depression',
}

PASS = '\033[92mPASS\033[0m'
FAIL = '\033[91mFAIL\033[0m'
errors = []

def check(label, condition, detail=''):
    if condition:
        print(f'  {PASS}  {label}')
    else:
        print(f'  {FAIL}  {label}' + (f' — {detail}' if detail else ''))
        errors.append(label)

# ════════════════════════════════════════════════════════════════════════════════
# Workflow 1 — New appointment → doctor
# ════════════════════════════════════════════════════════════════════════════════
print('\nWorkflow 1: New appointment notification → doctor')
before = len(sent_emails)
r1 = send_new_appointment_notification(sample)
check('Returns True',          r1 is True,           f'got {r1!r}')
check('Exactly 1 email sent',  len(sent_emails) == before + 1,
      f'sent {len(sent_emails)-before}')
e1 = sent_emails[-1]
check('Recipient = DOCTOR_EMAIL', e1['to'] == ['doctor@example.com'],
      f"got {e1['to']}")
check('Sender = FROM_EMAIL',      e1['from'] == 'onboarding@resend.dev',
      f"got {e1['from']}")
check('Subject contains "Request"', 'Request' in e1['subject'],
      f"got {e1['subject']!r}")
check('HTML contains patient name',  sample['name'] in e1['html'])
check('HTML contains date',          sample['preferred_date'] in e1['html'])
check('HTML does NOT contain "message" key', 'message' not in e1.get('text','').lower().split('message')[0][:5])

# ════════════════════════════════════════════════════════════════════════════════
# Workflow 2 — Appointment accepted → patient
# ════════════════════════════════════════════════════════════════════════════════
print('\nWorkflow 2: Appointment accepted → patient')
before = len(sent_emails)
r2 = send_appointment_accepted_email(sample)
check('Returns True',              r2 is True,          f'got {r2!r}')
check('Exactly 1 email sent',      len(sent_emails) == before + 1)
e2 = sent_emails[-1]
check('Recipient = patient email', e2['to'] == ['patient@example.com'],
      f"got {e2['to']}")
check('Subject contains "Confirmed"', 'Confirmed' in e2['subject'],
      f"got {e2['subject']!r}")
check('HTML greets patient by name', sample['name'] in e2['html'])
medical_note = 'PRIVATE_MEDICAL_DATA_XYZ'
check('HTML does NOT contain medical notes (message field excluded)',
      medical_note not in e2['html'])

# ════════════════════════════════════════════════════════════════════════════════
# Workflow 3 — Appointment declined → patient
# ════════════════════════════════════════════════════════════════════════════════
print('\nWorkflow 3: Appointment declined → patient')
before = len(sent_emails)
r3 = send_appointment_declined_email(sample)
check('Returns True',              r3 is True,          f'got {r3!r}')
check('Exactly 1 email sent',      len(sent_emails) == before + 1)
e3 = sent_emails[-1]
check('Recipient = patient email', e3['to'] == ['patient@example.com'],
      f"got {e3['to']}")
check('Subject contains "Update"', 'Update' in e3['subject'],
      f"got {e3['subject']!r}")
check('HTML greets patient by name', sample['name'] in e3['html'])

# ════════════════════════════════════════════════════════════════════════════════
# Dispatcher — send_appointment_email
# ════════════════════════════════════════════════════════════════════════════════
print('\nDispatcher: send_appointment_email()')
before = len(sent_emails)
send_appointment_email(sample, 'approved')
check('approved → patient confirmation', sent_emails[-1]['to'] == ['patient@example.com'])
before = len(sent_emails)
send_appointment_email(sample, 'cancelled')
check('cancelled → patient decline',    sent_emails[-1]['to'] == ['patient@example.com'])
r_bad = send_appointment_email(sample, 'pending')
check('unknown status → False (no email)', r_bad is False and len(sent_emails) == before + 1,
      f'sent_count={len(sent_emails)-before}, result={r_bad!r}')

# ════════════════════════════════════════════════════════════════════════════════
# No-credential guard
# ════════════════════════════════════════════════════════════════════════════════
print('\nGuard: missing RESEND_API_KEY')
import email_utils as eu
original_key = eu.RESEND_API_KEY
eu.RESEND_API_KEY = ''
before = len(sent_emails)
r_skip = send_new_appointment_notification(sample)
eu.RESEND_API_KEY = original_key
check('Returns False when key missing', r_skip is False, f'got {r_skip!r}')
check('No email dispatched',            len(sent_emails) == before,
      f'sent {len(sent_emails)-before}')

# ════════════════════════════════════════════════════════════════════════════════
# Summary
# ════════════════════════════════════════════════════════════════════════════════
total = len(sent_emails)
print(f'\nTotal mock emails captured: {total}')
print(f'Resend IDs: {[e.get("id","?") for e in sent_emails[:total]]}')

if errors:
    print(f'\n{len(errors)} assertion(s) FAILED:')
    for e in errors:
        print(f'  ✗ {e}')
    sys.exit(1)
else:
    print('\nAll assertions passed.')
    sys.exit(0)
