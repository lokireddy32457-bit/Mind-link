"""
Mind Link — Flask Application
Main entry point for the psychiatrist clinic website.
Serves public pages and admin dashboard with appointment management.
"""

import os
import secrets
import psycopg2
from datetime import datetime, timedelta
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
    get_booked_slots, cancel_appointments_by_date,
    get_site_settings, update_site_setting
)
from auth import (
    login_required, authenticate_admin, create_default_admin
)
from email_utils import send_appointment_email

app = Flask(__name__)

# =====================
# Security Configuration
# =====================
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Secure session cookies (HTTPS-only in production)
is_production = os.environ.get('FLASK_ENV', 'development') == 'production'
app.config['SESSION_COOKIE_SECURE'] = is_production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)


# =====================
# Template Context
# =====================

@app.context_processor
def inject_globals():
    """Inject commonly needed globals into all templates."""
    site = get_site_settings()
    return {
        'now': datetime.utcnow,
        'site_name': site.get('site_name', 'HELIUM MIND CENTRE'),
        'site_location': site.get('site_location', ''),
        'social_facebook': site.get('social_facebook', 'https://www.facebook.com/heliummindcenter'),
        'social_instagram': site.get('social_instagram', '#'),
        'social_whatsapp': site.get('social_whatsapp', 'https://api.whatsapp.com/send/?phone=919951432102'),
    }


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


# Service detail data
SERVICE_DATA = {
    'psychotherapy': {
        'slug': 'psychotherapy',
        'title': 'Individual Psychotherapy',
        'icon': '🗣️',
        'tagline': 'Personalized one-on-one therapy to help you understand patterns, heal, and thrive.',
        'image': 'service-psychotherapy.png',
        'overview': (
            'Individual psychotherapy at HELIUM MIND CENTRE is a deeply personal journey tailored '
            'to your unique needs, history, and goals. Our psychiatrist uses a collaborative approach, '
            'working alongside you to uncover root causes of distress, develop coping strategies, and '
            'build long-lasting emotional resilience.'
        ),
        'what_we_treat': [
            'Depression & persistent sadness',
            'Anxiety & excessive worry',
            'Low self-esteem & self-doubt',
            'Life transitions & adjustment issues',
            'Grief & loss',
            'Relationship and interpersonal difficulties',
        ],
        'approaches': [
            ('Cognitive Behavioral Therapy (CBT)', 'Identify and reshape unhelpful thought patterns that drive negative emotions and behaviors.'),
            ('Dialectical Behavior Therapy (DBT)', 'Develop emotional regulation, distress tolerance, and interpersonal effectiveness skills.'),
            ('Psychodynamic Therapy', 'Explore unconscious patterns and past experiences that shape your present behavior.'),
            ('Mindfulness-Based Techniques', 'Cultivate present-moment awareness to reduce stress and improve mental clarity.'),
        ],
        'session_info': '45–60 minute sessions | In-person & Telehealth available',
        'faq': [
            ('How often do I need to attend?', 'Typically once a week, though frequency is adjusted based on your needs and progress.'),
            ('Is everything confidential?', 'Yes, all sessions are strictly confidential and protected under HIPAA regulations.'),
            ('How soon will I see results?', 'Most patients notice meaningful improvements within 6–8 sessions, though this varies individually.'),
        ],
    },
    'medication': {
        'slug': 'medication',
        'title': 'Medication Management',
        'icon': '💊',
        'tagline': 'Expert psychiatric evaluation and ongoing medication monitoring for optimal wellbeing.',
        'image': 'service-medication.png',
        'overview': (
            'Psychiatric medications, when properly managed, can be life-changing. At HELIUM MIND CENTRE '
            'we conduct thorough evaluations before recommending any medication, ensuring the right treatment '
            'is matched to the right person. Our ongoing monitoring and open communication mean you are never '
            'navigating this journey alone.'
        ),
        'what_we_treat': [
            'Major Depressive Disorder',
            'Bipolar Disorder & Mania',
            'Schizophrenia & Psychosis',
            'Generalized Anxiety Disorder',
            'ADHD & Attention Difficulties',
            'OCD & related disorders',
        ],
        'approaches': [
            ('Comprehensive Evaluation', 'A thorough psychiatric assessment to understand your history, symptoms, and lifestyle before prescribing.'),
            ('Personalized Prescribing', 'Medications chosen specifically for you — not a one-size-fits-all approach.'),
            ('Ongoing Monitoring', 'Regular follow-ups to track effectiveness, adjust dosages, and manage side effects.'),
            ('Integrated Care', 'Medication management often paired with therapy for the best long-term outcomes.'),
        ],
        'session_info': '30–45 minute follow-up appointments | In-person & Telehealth',
        'faq': [
            ('Will I need medication forever?', 'Not necessarily. Many patients use medication short-term while developing coping skills through therapy.'),
            ('What if I experience side effects?', 'You should contact us immediately. We work closely with you to adjust or switch medications as needed.'),
            ('How long before the medication works?', 'Most psychiatric medications take 2–6 weeks to reach full effect, though some symptoms improve sooner.'),
        ],
    },
    'telehealth': {
        'slug': 'telehealth',
        'title': 'Telehealth / Virtual Sessions',
        'icon': '🖥️',
        'tagline': 'The same expert care — from the comfort, privacy, and convenience of your own home.',
        'image': 'service-telehealth.png',
        'overview': (
            'Our telehealth service brings world-class psychiatric care directly to you, wherever you are. '
            'Using a secure, HIPAA-compliant video platform, you can meet with our psychiatrist without the '
            'stress of commuting or waiting rooms. Telehealth sessions are equally effective for therapy, '
            'medication management, and initial evaluations.'
        ),
        'what_we_treat': [
            'All conditions treated in-person',
            'Remote follow-up appointments',
            'Initial psychiatric evaluations',
            'Medication reviews & renewals',
            'Crisis support & urgent consultations',
            'Ongoing psychotherapy sessions',
        ],
        'approaches': [
            ('Secure Video Platform', 'HIPAA-compliant, encrypted video calls accessible from any device.'),
            ('Flexible Scheduling', 'Early morning, evening, and weekend slots to fit your busy life.'),
            ('Same-Day Availability', 'Urgent and same-day slots often available for telehealth appointments.'),
            ('Multi-State Coverage', 'Available across all states where we hold licensure.'),
        ],
        'session_info': '45–60 minute sessions | Video, Phone, or Chat options',
        'faq': [
            ('What do I need for a telehealth session?', 'A device with a camera and microphone (smartphone, tablet, or computer) and a stable internet connection.'),
            ('Is telehealth as effective as in-person?', 'Research shows telehealth is equally effective for most psychiatric conditions.'),
            ('How do I join my session?', "You'll receive a secure link by email before your appointment — simply click to join."),
        ],
    },
    'anxiety': {
        'slug': 'anxiety',
        'title': 'Anxiety & Depression Treatment',
        'icon': '😰',
        'tagline': 'Evidence-based, compassionate care to help you reclaim joy, calm, and confidence.',
        'image': 'article-anxiety.png',
        'overview': (
            'Anxiety and depression are among the most common yet misunderstood conditions. At HELIUM MIND CENTRE, '
            'we combine the latest evidence-based therapies with personalized medication management to help you '
            'break free from the cycle of fear, sadness, and hopelessness. Recovery is possible — and we are with '
            'you every step of the way.'
        ),
        'what_we_treat': [
            'Generalized Anxiety Disorder (GAD)',
            'Social Anxiety & Phobias',
            'Major Depressive Disorder',
            'Panic Disorder & Panic Attacks',
            'Treatment-Resistant Depression',
            'Mixed Anxiety-Depression',
        ],
        'approaches': [
            ('Cognitive Behavioral Therapy', 'Challenge distorted thoughts and break cycles of avoidance that fuel anxiety and depression.'),
            ('Exposure Therapy', 'Gradually and safely face feared situations to reduce their power over you.'),
            ('Medication Evaluation', 'Antidepressants and anti-anxiety medications prescribed thoughtfully when clinically appropriate.'),
            ('Lifestyle & Wellness Coaching', 'Sleep hygiene, exercise, and nutrition guidance to support your mental health journey.'),
        ],
        'session_info': 'Weekly sessions recommended | In-person & Telehealth',
        'faq': [
            ('Can anxiety and depression be cured?', 'Most people achieve significant symptom relief and long-term remission with the right treatment.'),
            ('Do I need medication for depression?', 'Not always. Many patients respond well to therapy alone; medication is discussed case-by-case.'),
            ('How long does treatment take?', 'Many people see improvement in 8–16 sessions; some continue longer for lasting results.'),
        ],
    },
    'ptsd': {
        'slug': 'ptsd',
        'title': 'PTSD & Trauma Therapy',
        'icon': '💔',
        'tagline': 'Trauma-informed, evidence-based care to help you process the past and reclaim your life.',
        'image': 'service-ptsd.png',
        'overview': (
            'Trauma can leave invisible wounds that affect every aspect of your life. Our trauma-informed approach '
            'at HELIUM MIND CENTRE creates a safe, non-judgmental space where healing becomes possible. We use '
            'internationally recognized, evidence-based therapies to help you process traumatic memories, reduce '
            'distressing symptoms, and rebuild a sense of safety and control.'
        ),
        'what_we_treat': [
            'Post-Traumatic Stress Disorder (PTSD)',
            'Complex PTSD (C-PTSD)',
            'Childhood trauma & abuse',
            'Grief & complicated bereavement',
            'Trauma from accidents or disaster',
            'Veterans & first responder trauma',
        ],
        'approaches': [
            ('Trauma-Focused CBT (TF-CBT)', 'Process traumatic memories and develop coping skills in a structured, evidence-based framework.'),
            ('EMDR Therapy', 'Eye Movement Desensitization and Reprocessing to reduce the emotional charge of traumatic memories.'),
            ('Somatic Techniques', 'Body-centered approaches to release trauma stored in the nervous system.'),
            ('Prolonged Exposure Therapy', 'Gradually process trauma-related memories and situations to reduce avoidance and distress.'),
        ],
        'session_info': '60–90 minute sessions | In-person strongly recommended',
        'faq': [
            ('Will I have to relive my trauma?', 'Therapy is always at your pace. We never push you to discuss anything before you feel ready.'),
            ('What is EMDR?', 'EMDR uses guided eye movements to help the brain reprocess traumatic memories, reducing their emotional impact.'),
            ('Can trauma therapy make things worse first?', 'Temporarily, some discomfort is normal as you begin processing. Your therapist will support you throughout.'),
        ],
    },
    'child': {
        'slug': 'child',
        'title': 'Child & Adolescent Psychiatry',
        'icon': '👨‍👩‍👧',
        'tagline': 'Age-appropriate, family-inclusive care for young minds navigating emotional and behavioral challenges.',
        'image': 'service-child-psychiatry.png',
        'overview': (
            'Children and adolescents face unique mental health challenges that require a specialized, compassionate '
            'approach. HELIUM MIND CENTRE provides comprehensive psychiatric care for young people aged 5–17, working '
            'closely with families, schools, and other caregivers to create a holistic support system around every child.'
        ),
        'what_we_treat': [
            'ADHD & Attention Difficulties',
            'Childhood Anxiety & OCD',
            'Depression in children & teens',
            'Behavioral & Conduct Disorders',
            'Autism Spectrum Disorder support',
            'School refusal & social difficulties',
        ],
        'approaches': [
            ('Child-Friendly Therapy', 'Play therapy and age-appropriate techniques that engage children in meaningful ways.'),
            ('Family Therapy & Psychoeducation', 'Empowering parents with tools and understanding to support their child at home.'),
            ('School Collaboration', 'Communication with educators to create supportive academic environments.'),
            ('Adolescent-Focused CBT', 'Evidence-based therapy adapted specifically for teenagers navigating identity and emotion.'),
        ],
        'session_info': '45–60 minute sessions | Family involvement encouraged',
        'faq': [
            ('At what age can my child start therapy?', 'We typically work with children from age 5 and adolescents up to age 17.'),
            ('Will parents be involved in sessions?', 'Yes — parental involvement is a core part of our child and adolescent approach.'),
            ('Is medication safe for children?', 'Pediatric medication is prescribed conservatively, only when clearly beneficial, and carefully monitored.'),
        ],
    },
    'insomnia': {
        'slug': 'insomnia',
        'title': 'Insomnia & Sleep Disorders',
        'icon': '🌙',
        'tagline': 'Reclaim restful nights and energized days with targeted, evidence-based sleep treatment.',
        'image': 'service-insomnia.png',
        'overview': (
            'Poor sleep affects every aspect of mental and physical health. At HELIUM MIND CENTRE, we treat '
            'insomnia and sleep disorders using both behavioral and pharmacological approaches, always starting '
            'with the least invasive, most sustainable option. Our goal is to help you achieve deep, restorative '
            'sleep naturally and consistently.'
        ),
        'what_we_treat': [
            'Chronic Insomnia',
            'Sleep Maintenance Issues',
            'Sleep Anxiety & Hyperarousal',
            'Nightmare Disorder',
            'Sleep Disruption from Depression/Anxiety',
            'Medication-related sleep issues',
        ],
        'approaches': [
            ('CBT for Insomnia (CBT-I)', 'The gold-standard, non-medication treatment that addresses the root causes of chronic insomnia.'),
            ('Sleep Hygiene Optimization', 'Personalized behavioral changes to strengthen your body\'s natural sleep drive.'),
            ('Relaxation Techniques', 'Progressive muscle relaxation, guided imagery, and breathing exercises for bedtime.'),
            ('Short-Term Medication', 'Safe, carefully managed sleep medications for acute cases when behavioral approaches need support.'),
        ],
        'session_info': '45–60 minute sessions | Telehealth very suitable',
        'faq': [
            ('What is CBT-I?', 'Cognitive Behavioral Therapy for Insomnia — the most effective long-term treatment for chronic insomnia, without medications.'),
            ('How many sessions will I need?', 'CBT-I typically requires 6–8 sessions for most patients to achieve lasting improvement.'),
            ('Are sleep medications addictive?', 'Some can be habit-forming; we prescribe cautiously and always aim to minimize or eliminate medication use.'),
        ],
    },
    'adhd': {
        'slug': 'adhd',
        'title': 'ADHD Behavioural',
        'icon': '🧩',
        'tagline': 'Comprehensive ADHD evaluation and tailored strategies to help you focus, organize, and excel.',
        'image': 'article-adhd.png',
        'overview': (
            'ADHD is a neurodevelopmental condition that affects attention, impulse control, and executive functioning. '
            'Far from a simple focus issue, ADHD can impact academic performance, relationships, career, and self-esteem. '
            'HELIUM MIND CENTRE offers thorough ADHD evaluation and a comprehensive treatment plan that may include '
            'behavioral strategies, therapy, coaching, and medication when appropriate.'
        ),
        'what_we_treat': [
            'ADHD — Inattentive type',
            'ADHD — Hyperactive-Impulsive type',
            'Combined presentation ADHD',
            'Adult ADHD (late diagnosis)',
            'ADHD with co-occurring anxiety or depression',
            'Academic & occupational impairment',
        ],
        'approaches': [
            ('Comprehensive ADHD Evaluation', 'Detailed diagnostic assessment using rating scales, clinical interview, and history to confirm diagnosis.'),
            ('Behavioral Coaching', 'Practical strategies for organization, time management, task initiation, and emotional regulation.'),
            ('Medication Management', 'Stimulant and non-stimulant medications carefully prescribed and monitored.'),
            ('CBT for ADHD', 'Cognitive-behavioral techniques to address the thinking patterns and habits that ADHD creates.'),
        ],
        'session_info': 'Evaluation + ongoing sessions | In-person & Telehealth',
        'faq': [
            ('Can adults have ADHD?', 'Absolutely. Many adults are diagnosed later in life; treatment is highly effective at any age.'),
            ('Does ADHD always need medication?', 'No. Behavioral therapy and coaching can be very effective, especially for milder presentations.'),
            ('How is ADHD diagnosed?', 'Through a comprehensive clinical evaluation — there is no single test; it requires thorough history-taking and assessment.'),
        ],
    },
}


@app.route('/services/<slug>')
def service_detail(slug):
    """Individual service detail page."""
    service = SERVICE_DATA.get(slug)
    if not service:
        return redirect(url_for('services'))
    return render_template('service_detail.html', service=service)


@app.route('/booking')
def booking():
    """Booking and contact page."""
    # Slug-to-service_type mapping for autofill from service pages
    SERVICE_SLUG_MAP = {
        'psychotherapy': 'psychotherapy',
        'medication': 'medication_management',
        'telehealth': 'telehealth',
        'anxiety': 'anxiety_depression',
        'ptsd': 'ptsd_trauma',
        'child': 'child_adolescent',
        'insomnia': 'insomnia',
        'adhd': 'adhd',
    }
    preselect_service = SERVICE_SLUG_MAP.get(request.args.get('service', '').strip(), '')
    return render_template('booking.html', preselect_service=preselect_service)


@app.route('/api/booked-slots')
def api_booked_slots():
    """Public JSON endpoint: returns approved time slots for a given date."""
    date = request.args.get('date', '').strip()
    if not date:
        return jsonify({'booked': []})
    booked = get_booked_slots(date)
    return jsonify({'booked': booked})


@app.route('/health')
def health_check():
    """Liveness endpoint for Nginx, load balancers, and monitoring tools.

    Returns HTTP 200 when the application process is running.
    Does NOT query the database or expose internal infrastructure details.
    """
    return jsonify({'status': 'ok', 'service': 'mindlink'}), 200


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


@app.route('/admin/settings')
@login_required
def admin_settings():
    """Dedicated settings page with per-page configuration tabs."""
    settings = get_site_settings()
    return render_template('admin/settings.html', settings=settings)


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


@app.route('/admin/appointments/cancel-by-date', methods=['POST'])
@login_required
def cancel_appointments_by_date_route():
    """Cancel all pending/approved appointments on a selected date."""
    data = request.get_json() or {}
    date = data.get('date', '').strip()

    if not date:
        return jsonify({'success': False, 'message': 'Date is required.'}), 400

    # Validate date format
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format.'}), 400

    cancelled = cancel_appointments_by_date(date)
    count = len(cancelled)

    # Send cancellation emails for each affected appointment
    email_failures = 0
    for apt in cancelled:
        try:
            send_appointment_email(apt, 'cancelled')
        except Exception:
            email_failures += 1

    message = f'{count} appointment(s) cancelled for {date}.'
    if email_failures:
        message += f' ({email_failures} notification email(s) failed.)'

    return jsonify({'success': True, 'message': message, 'count': count})


@app.route('/admin/api/stats')
@login_required
def api_stats():
    """JSON endpoint for dashboard statistics."""
    stats = get_dashboard_stats()
    return jsonify(stats)


@app.route('/admin/api/settings', methods=['POST'])
@login_required
def api_update_settings():
    """Update site settings (hospital name and location) via AJAX."""
    data = request.get_json() or {}
    allowed_keys = {
        # General / clinic identity
        'site_name', 'site_location', 'site_phone', 'site_email',
        'hours_weekday', 'hours_weekend',
        # Social
        'social_facebook', 'social_instagram', 'social_whatsapp',
        # Home page
        'home_hero_title', 'home_hero_subtitle',
        'home_hero_cta_primary', 'home_hero_cta_secondary',
        'home_stat1_number', 'home_stat1_label',
        'home_stat2_number', 'home_stat2_label',
        'home_stat3_number', 'home_stat3_label',
        'home_whyus_title', 'home_whyus_subtitle',
        'home_show_telehealth_banner', 'home_show_testimonials', 'home_show_articles',
        # About page
        'about_doctor_name', 'about_doctor_credentials', 'about_doctor_title',
        'about_doctor_bio', 'about_doctor_experience', 'about_doctor_languages',
        'about_page_title', 'about_page_tagline',
        'about_show_photo', 'about_show_qualifications', 'about_show_awards',
        # Services page
        'services_page_title', 'services_page_subtitle',
        'services_show_psychotherapy', 'services_show_medication', 'services_show_telehealth',
        'services_show_anxiety', 'services_show_ptsd', 'services_show_child',
        'services_show_insomnia', 'services_show_adhd',
        'services_consultation_fee', 'services_followup_fee', 'services_insurance_note',
        # Booking page
        'booking_page_title', 'booking_page_subtitle',
        'booking_slot_start', 'booking_slot_end', 'booking_slot_duration',
        'booking_advance_days', 'booking_available_days',
        'booking_require_message', 'booking_allow_telehealth', 'booking_accepting_patients',
        'booking_success_message',
        # Contact page
        'contact_page_title', 'contact_page_subtitle',
        'contact_phone', 'contact_phone2', 'contact_email', 'contact_maps_embed',
        'contact_hours_weekday', 'contact_hours_weekend',
        'contact_show_map', 'contact_show_form', 'contact_show_whatsapp',
    }
    # Required fields that must not be blank
    REQUIRED_KEYS = {'site_name', 'site_location'}

    errors = []
    updated = []

    for key in allowed_keys:
        if key not in data:
            continue
        value = str(data[key]).strip()
        # Enforce non-empty only for required fields; skip empty optional fields silently
        if not value:
            if key in REQUIRED_KEYS:
                errors.append(f'{key} cannot be empty.')
            continue
        try:
            update_site_setting(key, value)
            updated.append(key)
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            return jsonify({
                'success': False,
                'message': 'Database connection timed out. The database may be waking up — please wait a moment and try again.'
            }), 503
        except Exception as e:
            errors.append(str(e))

    if errors:
        return jsonify({'success': False, 'message': ' '.join(errors)}), 400

    return jsonify({'success': True, 'message': f'Settings saved successfully ({len(updated)} updated).'})


# =====================
# Run the application
# =====================

if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(debug=debug, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
