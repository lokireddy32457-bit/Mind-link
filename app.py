"""
Mind Link — Flask Application
Main entry point for the psychiatrist clinic website.
Serves public pages and admin dashboard with appointment management.
"""

import os
import secrets
from dotenv import load_dotenv

load_dotenv()  # Load .env file into environment variables

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, jsonify
)
from database import (
    init_db, save_appointment, save_inquiry,
    get_appointments, get_appointment_by_id,
    update_appointment_status, get_dashboard_stats,
    get_booked_slots
)
from auth import (
    login_required, authenticate_admin, create_default_admin
)
from email_utils import send_appointment_email

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))


# =====================
# Initialize on startup
# =====================
with app.app_context():
    init_db()
    create_default_admin()


# =====================
# Public Routes
# =====================

@app.route('/')
def home():
    """Home page with hero, highlights, and CTA."""
    return render_template('index.html')


@app.route('/about')
def about():
    """About the Doctor page."""
    return render_template('about.html')


@app.route('/services')
def services():
    """Services overview page."""
    return render_template('services.html')


@app.route('/booking')
def booking():
    """Booking and contact page."""
    return render_template('booking.html')


@app.route('/api/booked-slots')
def api_booked_slots():
    """Public JSON endpoint: returns approved time slots for a given date."""
    date = request.args.get('date', '').strip()
    if not date:
        return jsonify({'booked': []})
    booked = get_booked_slots(date)
    return jsonify({'booked': booked})


# =====================
# Form Submission Routes
# =====================

@app.route('/booking', methods=['POST'])
def submit_booking():
    """Handle appointment booking form submission."""
    # Collect form data
    data = {
        'name': request.form.get('name', '').strip(),
        'email': request.form.get('email', '').strip(),
        'phone': request.form.get('phone', '').strip(),
        'preferred_date': request.form.get('preferred_date', '').strip(),
        'preferred_time': request.form.get('preferred_time', '').strip(),
        'service_type': request.form.get('service_type', '').strip(),
        'message': request.form.get('message', '').strip()
    }

    # Server-side validation
    errors = []
    if not data['name']:
        errors.append('Name is required.')
    if not data['email'] or '@' not in data['email']:
        errors.append('A valid email address is required.')
    phone_digits = ''.join(c for c in data['phone'] if c.isdigit())
    if not data['phone']:
        errors.append('Phone number is required.')
    elif len(phone_digits) != 10:
        errors.append('Phone number must contain exactly 10 digits.')
    if not data['preferred_date']:
        errors.append('Preferred date is required.')
    if not data['preferred_time']:
        errors.append('Preferred time is required.')
    if not data['service_type']:
        errors.append('Please select a service.')

    # Check if the time slot is already booked (approved)
    if data['preferred_date'] and data['preferred_time']:
        booked = get_booked_slots(data['preferred_date'])
        if data['preferred_time'] in booked:
            errors.append('This time slot is already booked. Please choose a different time.')

    if errors:
        for error in errors:
            flash(error, 'error')
        return render_template('booking.html', form_data=data), 400

    # Save to database
    try:
        save_appointment(data)
        flash('Your appointment request has been submitted successfully! We will contact you shortly to confirm.', 'success')
    except Exception as e:
        flash('An error occurred while processing your request. Please try again.', 'error')
        print(f'Database error: {e}')

    return redirect(url_for('booking'))


@app.route('/contact')
def contact():
    """Contact page with message form and location info."""
    return render_template('contact.html')


@app.route('/contact', methods=['POST'])
def submit_contact():
    """Handle general contact form submission."""
    data = {
        'name': request.form.get('contact_name', '').strip(),
        'email': request.form.get('contact_email', '').strip(),
        'subject': request.form.get('contact_subject', '').strip(),
        'message': request.form.get('contact_message', '').strip()
    }

    # Server-side validation
    errors = []
    if not data['name']:
        errors.append('Name is required.')
    if not data['email'] or '@' not in data['email']:
        errors.append('A valid email address is required.')
    if not data['subject']:
        errors.append('Subject is required.')
    if not data['message']:
        errors.append('Message is required.')

    if errors:
        for error in errors:
            flash(error, 'error')
        return redirect(url_for('contact'))

    try:
        save_inquiry(data)
        flash('Your message has been sent successfully! We will get back to you soon.', 'success')
    except Exception as e:
        flash('An error occurred while sending your message. Please try again.', 'error')
        print(f'Database error: {e}')

    return redirect(url_for('contact'))


# =====================
# Admin Routes
# =====================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page and authentication."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if authenticate_admin(username, password):
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Welcome back, Doctor!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    """Clear admin session and redirect to login."""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin_login'))


@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard — appointment management."""
    # Get filter parameters
    status = request.args.get('status', 'all')
    service_type = request.args.get('service_type', 'all')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    appointments = get_appointments(
        status=status,
        service_type=service_type,
        date_from=date_from if date_from else None,
        date_to=date_to if date_to else None
    )
    stats = get_dashboard_stats()

    return render_template('admin/dashboard.html',
                           appointments=appointments,
                           stats=stats,
                           filters={
                               'status': status,
                               'service_type': service_type,
                               'date_from': date_from,
                               'date_to': date_to
                           })


@app.route('/admin/appointments/<int:appointment_id>/approve', methods=['POST'])
@login_required
def approve_appointment(appointment_id):
    """Approve an appointment and notify the patient via email."""
    appointment = get_appointment_by_id(appointment_id)
    if not appointment:
        return jsonify({'success': False, 'message': 'Appointment not found.'}), 404

    update_appointment_status(appointment_id, 'approved')

    # Send confirmation email to patient
    email_sent = send_appointment_email(appointment, 'approved')
    message = 'Appointment approved successfully.'
    if email_sent:
        message += ' A confirmation email has been sent to the patient.'

    return jsonify({'success': True, 'message': message, 'new_status': 'approved', 'email_sent': email_sent})


@app.route('/admin/appointments/<int:appointment_id>/cancel', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    """Cancel an appointment and notify the patient via email."""
    appointment = get_appointment_by_id(appointment_id)
    if not appointment:
        return jsonify({'success': False, 'message': 'Appointment not found.'}), 404

    update_appointment_status(appointment_id, 'cancelled')

    # Send cancellation email to patient
    email_sent = send_appointment_email(appointment, 'cancelled')
    message = 'Appointment cancelled.'
    if email_sent:
        message += ' A cancellation email has been sent to the patient.'

    return jsonify({'success': True, 'message': message, 'new_status': 'cancelled', 'email_sent': email_sent})


@app.route('/admin/api/stats')
@login_required
def api_stats():
    """JSON endpoint for dashboard statistics."""
    stats = get_dashboard_stats()
    return jsonify(stats)


# =====================
# Run the application
# =====================

if __name__ == '__main__':
    app.run(debug=True, port=5000)
