/**
 * Mind Link — EmailJS Configuration
 * ===================================
 * 
 * HOW TO SET UP:
 * 1. Go to https://www.emailjs.com and create a free account
 * 2. Add an Email Service (e.g., Gmail, Outlook) — copy the Service ID
 * 3. Create an Email Template with these template variables:
 *      {{patient_name}}
 *      {{patient_email}}
 *      {{patient_phone}}
 *      {{service_type}}
 *      {{preferred_date}}
 *      {{preferred_time}}
 *      {{message}}
 *      {{booking_timestamp}}
 * 4. Copy your Template ID and Public Key from the EmailJS dashboard
 * 5. Replace the placeholder values below with your actual credentials
 */

var EMAILJS_CONFIG = {
    PUBLIC_KEY:   '9NzeteAAvwOrQkkcZ',         // Dashboard → Account → API Keys → Public Key
    SERVICE_ID:   'service_zvn2yfl',           // Dashboard → Email Services → Service ID
    TEMPLATE_ID:  'template_vlambw8'           // Dashboard → Email Templates → Template ID
};


/**
 * Map service_type form values to human-readable labels
 */
var SERVICE_LABELS = {
    'initial_consultation':   'Initial Consultation',
    'psychotherapy':          'Individual Psychotherapy',
    'medication_management':  'Medication Management',
    'telehealth':             'Telehealth Session',
    'anxiety_depression':     'Anxiety & Depression Treatment',
    'ptsd_trauma':            'PTSD & Trauma Therapy',
    'child_adolescent':       'Child & Adolescent Psychiatry',
    'other':                  'Other'
};


/**
 * Send appointment details via EmailJS.
 * Called after client-side validation passes, before the form submits to the server.
 *
 * @param {HTMLFormElement} form - The booking form element
 * @returns {Promise} - Resolves on success, rejects on failure
 */
function sendAppointmentEmail(form) {
    // Check if EmailJS is loaded and configured
    if (typeof emailjs === 'undefined') {
        console.warn('[EmailJS] SDK not loaded — skipping email notification.');
        return Promise.resolve();
    }

    if (EMAILJS_CONFIG.PUBLIC_KEY === 'YOUR_PUBLIC_KEY_HERE') {
        console.warn('[EmailJS] Credentials not configured — skipping email notification.');
        console.info('[EmailJS] Edit static/js/emailjs-config.js with your EmailJS credentials.');
        return Promise.resolve();
    }

    // Gather form data
    var serviceRaw = form.querySelector('#service_type').value;
    var serviceLabel = SERVICE_LABELS[serviceRaw] || serviceRaw;

    var preferredDate = form.querySelector('#preferred_date').value;
    var preferredTime = form.querySelector('#preferred_time').value;

    // Format date nicely (e.g., "May 31, 2026")
    var formattedDate = preferredDate;
    try {
        var dateObj = new Date(preferredDate + 'T00:00:00');
        formattedDate = dateObj.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    } catch (e) { /* keep raw date */ }

    // Format time nicely (e.g., "2:30 PM")
    var formattedTime = preferredTime;
    try {
        var timeParts = preferredTime.split(':');
        var hours = parseInt(timeParts[0]);
        var minutes = timeParts[1];
        var ampm = hours >= 12 ? 'PM' : 'AM';
        hours = hours % 12 || 12;
        formattedTime = hours + ':' + minutes + ' ' + ampm;
    } catch (e) { /* keep raw time */ }

    // Build the template parameters
    var templateParams = {
        patient_name:      form.querySelector('#name').value.trim(),
        patient_email:     form.querySelector('#email').value.trim(),
        patient_phone:     form.querySelector('#phone').value.trim(),
        service_type:      serviceLabel,
        preferred_date:    formattedDate,
        preferred_time:    formattedTime,
        message:           (form.querySelector('#message').value || '').trim() || 'No additional notes provided.',
        booking_timestamp: new Date().toLocaleString('en-US', {
            dateStyle: 'full',
            timeStyle: 'short'
        })
    };

    console.log('[EmailJS] Sending appointment notification...');

    return emailjs.send(
        EMAILJS_CONFIG.SERVICE_ID,
        EMAILJS_CONFIG.TEMPLATE_ID,
        templateParams
    )
    .then(function (response) {
        console.log('[EmailJS] ✅ Email sent successfully!', response.status, response.text);
        return response;
    })
    .catch(function (error) {
        console.error('[EmailJS] ❌ Failed to send email:', error);
        // Don't block form submission — the server-side save is the source of truth
        return Promise.resolve();
    });
}
