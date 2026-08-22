"""
Apply all required text changes to Mind Link templates cleanly.
Uses Python's utf-8 encoding throughout to avoid mojibake.
"""
import os

def replace_in_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Updated: {filepath}')

BRAND = [
    ('Mind Link Psychiatry', 'HELIUM MIND CENTRE'),
    ('Mind Link', 'HELIUM MIND CENTRE'),
]

# ── base.html ─────────────────────────────────────────────────────────────────
replace_in_file('templates/base.html', BRAND)

# ── index.html ────────────────────────────────────────────────────────────────
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Brand
for old, new in BRAND:
    content = content.replace(old, new)

# Hero section – name label above h1
content = content.replace(
    '✨ Now Accepting New Patients\n                </div>\n                <h1>Expert Psychiatric Care for a <span>Healthier Mind</span></h1>\n                <p>Compassionate, confidential and expert care for depression, anxiety, stress, addiction, ADHD and other mental health concerns.</p>',
    '✨ Now Accepting New Patients\n                </div>\n                <p style="font-size:1rem;font-weight:600;letter-spacing:0.08em;opacity:0.75;margin-bottom:0.25rem;">DR. VIKRAM AKAVARAM</p>\n                <h1>Dedicated Neuropsychiatrist Committed to <span>Holistic Mental Health Care</span></h1>\n                <p>MBBS, DPM (Osm) &bull; Neuro Psychiatrist &bull; Helium Mind Center — Specializing in comprehensive treatment of mental health disorders through an integrated mind &amp; brain approach.</p>'
)

# Hero stats
content = content.replace(
    '<span class="hero-stat-number">17+</span>\n                        <p class="hero-stat-label">Years Experience</p>',
    '<span class="hero-stat-number">MBBS</span>\n                        <p class="hero-stat-label">DPM (Osm)</p>'
)
content = content.replace(
    '<span class="hero-stat-number">1000+</span>\n                        <p class="hero-stat-label">Patients Helped</p>',
    '<span class="hero-stat-number">Neuro</span>\n                        <p class="hero-stat-label">Psychiatrist</p>'
)
content = content.replace(
    '<span class="hero-stat-number">Online &amp; In&#8209;Clinic</span>\n                        <p class="hero-stat-label">Consultations</p>',
    '<span class="hero-stat-number">Holistic</span>\n                        <p class="hero-stat-label">Approach</p>'
)
content = content.replace(
    '<span class="hero-stat-number">Personalized</span>\n                        <p class="hero-stat-label">Care for Every Patient</p>',
    '<span class="hero-stat-number">Helium</span>\n                        <p class="hero-stat-label">Mind Center</p>'
)

# Doctor intro section
content = content.replace(
    '<h2>Dr. Vikarn</h2>\n            <p>MBBS, DPM (Psychiatry) — Neuro Psychiatrist</p>',
    '<h2>Dr. Vikram Akavaram</h2>\n            <p>MBBS, DPM (Osm) — Neuro Psychiatrist</p>'
)
content = content.replace(
    'alt="Dr. Vikarn — Board-Certified Psychiatrist">',
    'alt="Dr. Vikram Akavaram — MBBS, DPM (Osm) Neuro Psychiatrist">'
)
content = content.replace(
    '<div class="doctor-intro-badge">🩺 Board Certified</div>',
    '<div class="doctor-intro-badge">🩺 Neuro Psychiatrist</div>'
)
content = content.replace(
    '<h3>Dr. Vikarn, <span>MD</span></h3>',
    '<h3>Dr. Vikram Akavaram, <span>MBBS, DPM (Osm)</span></h3>'
)
content = content.replace(
    '<p class="doctor-credential">Board-Certified Psychiatrist &bull; 17+ Years of Experience</p>',
    '<p class="doctor-credential">Neuro Psychiatrist &bull; Helium Mind Center</p>'
)
content = content.replace(
    '<p>With over 17+ years of experience, Dr. Vikarn provides comprehensive and individualized psychiatric care for patients across all age groups.</p>',
    '<p>Dr. Vikram Akavaram is a highly committed neuropsychiatrist specializing in the comprehensive treatment of mental health disorders. His holistic approach integrates the complexities of both mind and brain, leveraging extensive expertise in psychology and neurology to provide personalized and effective care for each patient.</p>'
)
content = content.replace(
    'Know More About Dr. Vikarn',
    'Know More About Dr. Akavaram'
)
content = content.replace(
    'alt="Dr. Vikarn — Board-Certified Psychiatrist"',
    'alt="Dr. Vikram Akavaram — MBBS, DPM (Osm) Neuro Psychiatrist"'
)

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated: templates/index.html')

# ── about.html ────────────────────────────────────────────────────────────────
with open('templates/about.html', 'r', encoding='utf-8') as f:
    content = f.read()

for old, new in BRAND:
    content = content.replace(old, new)

content = content.replace(
    '{% block title %}About Dr. Vikarn — Mind Link Psychiatry{% endblock %}',
    '{% block title %}About Dr. Vikram Akavaram — HELIUM MIND CENTRE{% endblock %}'
)
content = content.replace(
    '{% block description %}Learn about Dr. Vikarn — a board-certified psychiatrist with over 15 years of experience in compassionate, evidence-based mental health care.{% endblock %}',
    '{% block description %}Learn about Dr. Vikram Akavaram, MBBS, DPM (Osm) — a dedicated Neuro Psychiatrist at Helium Mind Center, committed to holistic mental health care.{% endblock %}'
)
content = content.replace(
    'alt="Dr. Vikarn — Board-Certified Psychiatrist">',
    'alt="Dr. Vikram Akavaram — MBBS, DPM (Osm) Neuro Psychiatrist">'
)
content = content.replace(
    '<h1>Dr. Vikarn</h1>',
    '<h1>Dr. Vikram Akavaram, <span style="font-size:0.7em;font-weight:500;">MBBS, DPM (Osm)</span></h1>'
)
content = content.replace(
    '<p class="credential">Board-Certified Psychiatrist &bull; 15+ Years of Experience</p>',
    '<p class="credential">Neuro Psychiatrist &bull; Helium Mind Center</p>'
)
content = content.replace(
    "<p>Dr. Vikarn is a compassionate and experienced psychiatrist dedicated to helping individuals achieve lasting mental wellness. With a patient-centered approach, she combines the latest advancements in psychiatric medicine with genuine empathy to provide care that truly makes a difference.</p>",
    "<p>Dr. Vikram Akavaram is a highly committed neuropsychiatrist specializing in the comprehensive treatment of mental health disorders. With a strong foundation in neuropsychiatry, he brings a unique perspective to the diagnosis and management of psychiatric conditions.</p>"
)
content = content.replace(
    "<p>After completing her medical degree at Johns Hopkins University School of Medicine and her psychiatry residency at Massachusetts General Hospital, Dr. Vikarn went on to specialize in mood disorders, anxiety, and trauma-related conditions.</p>",
    "<p>His holistic approach integrates the complexities of both mind and brain, leveraging extensive expertise in psychology and neurology to provide personalized and effective care for each patient.</p>"
)
content = content.replace(
    "<p>Dr. Vikarn specializes in a wide range of psychiatric conditions, providing tailored treatment plans for each patient.</p>",
    "<p>Dr. Akavaram specializes in a wide range of neuropsychiatric conditions, providing tailored treatment plans for each patient.</p>"
)
content = content.replace(
    "<p>Dr. Vikarn's extensive training and affiliations ensure the highest standard of psychiatric care.</p>",
    "<p>Dr. Akavaram's extensive training and commitment ensure the highest standard of neuropsychiatric care.</p>"
)
content = content.replace(
    '<h4>Johns Hopkins University</h4>\n                    <p>Doctor of Medicine (MD)</p>',
    '<h4>Osmania University</h4>\n                    <p>MBBS &amp; DPM (Psychiatry)</p>'
)
content = content.replace(
    '<h4>Massachusetts General Hospital</h4>\n                    <p>Psychiatry Residency</p>',
    '<h4>Helium Mind Center</h4>\n                    <p>Practicing Neuro Psychiatrist</p>'
)
content = content.replace(
    '<h4>American Board of Psychiatry</h4>\n                    <p>Board Certified — Psychiatry</p>',
    '<h4>Neuropsychiatry Specialist</h4>\n                    <p>Certified Neuro Psychiatrist</p>'
)
content = content.replace(
    '<h4>American Psychiatric Association</h4>\n                    <p>Distinguished Fellow</p>',
    '<h4>Indian Psychiatric Society</h4>\n                    <p>Member</p>'
)
content = content.replace(
    '<h2>Meet Dr. Vikarn in Person</h2>',
    '<h2>Meet Dr. Akavaram in Person</h2>'
)
content = content.replace(
    '<p>Schedule your initial consultation and discover a partner in your journey to mental wellness.</p>',
    '<p>Schedule your initial consultation and discover a dedicated neuropsychiatrist committed to your holistic mental health journey.</p>'
)
content = content.replace(
    '<p>At Mind Link, we believe that mental health care should be accessible, compassionate, and rooted in science.</p>',
    '<p>At HELIUM MIND CENTRE, we believe that mental health care should be accessible, compassionate, and rooted in science.</p>'
)

with open('templates/about.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated: templates/about.html')

# ── services, contact, booking, admin ─────────────────────────────────────────
for tmpl in ['templates/services.html', 'templates/contact.html',
             'templates/booking.html', 'templates/admin/login.html',
             'templates/admin/dashboard.html']:
    replace_in_file(tmpl, BRAND)

print('\nAll done! No PowerShell encoding involved.')
