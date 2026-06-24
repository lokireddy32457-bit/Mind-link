/**
 * Mind Link — Dashboard JavaScript
 * Handles stat counters, approve/cancel AJAX actions, confirmation modal, and auto-refresh.
 */

document.addEventListener('DOMContentLoaded', function () {

    // ========================================
    // Animated Stat Counters
    // ========================================
    const counters = document.querySelectorAll('.stat-counter');

    function animateCounter(el) {
        const target = parseInt(el.dataset.target) || 0;
        const duration = 1200;
        const startTime = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            // Ease out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            el.textContent = Math.round(target * eased);

            if (progress < 1) {
                requestAnimationFrame(update);
            } else {
                el.textContent = target;
            }
        }

        requestAnimationFrame(update);
    }

    counters.forEach(function (counter) {
        animateCounter(counter);
    });

    // ========================================
    // Auto-dismiss Flash Messages
    // ========================================
    const flashes = document.querySelectorAll('.flash');
    flashes.forEach(function (flash) {
        setTimeout(function () {
            flash.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            flash.style.opacity = '0';
            flash.style.transform = 'translateX(40px)';
            setTimeout(function () { flash.remove(); }, 300);
        }, 5000);
    });

    // ========================================
    // Auto-Refresh (every 60 seconds)
    // ========================================
    let autoRefreshInterval = setInterval(function () {
        // Only refresh if no modal is open
        const modal = document.getElementById('cancelModal');
        if (modal && !modal.classList.contains('active')) {
            location.reload();
        }
    }, 60000);

});


// ========================================
// Approve Appointment (AJAX)
// ========================================
function approveAppointment(appointmentId) {
    fetch('/admin/appointments/' + appointmentId + '/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(function (response) { return response.json(); })
    .then(function (data) {
        if (data.success) {
            updateAppointmentUI(appointmentId, 'approved');
            showToast('✅ Appointment approved successfully!', 'success');
            refreshStats();
        } else {
            showToast('❌ ' + data.message, 'error');
        }
    })
    .catch(function (err) {
        console.error('Error:', err);
        showToast('❌ An error occurred. Please try again.', 'error');
    });
}


// ========================================
// Cancel Appointment (with Modal)
// ========================================
let pendingCancelId = null;

function showCancelModal(appointmentId, patientName) {
    pendingCancelId = appointmentId;
    document.getElementById('cancelPatientName').textContent = patientName;
    document.getElementById('cancelModal').classList.add('active');

    // Set up confirm button
    document.getElementById('confirmCancelBtn').onclick = function () {
        cancelAppointment(pendingCancelId);
        closeCancelModal();
    };
}

function closeCancelModal() {
    document.getElementById('cancelModal').classList.remove('active');
    pendingCancelId = null;
}

function cancelAppointment(appointmentId) {
    fetch('/admin/appointments/' + appointmentId + '/cancel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(function (response) { return response.json(); })
    .then(function (data) {
        if (data.success) {
            updateAppointmentUI(appointmentId, 'cancelled');
            showToast('Appointment cancelled.', 'info');
            refreshStats();
        } else {
            showToast('❌ ' + data.message, 'error');
        }
    })
    .catch(function (err) {
        console.error('Error:', err);
        showToast('❌ An error occurred. Please try again.', 'error');
    });
}

// Close modal on overlay click
document.addEventListener('click', function (e) {
    if (e.target.id === 'cancelModal') {
        closeCancelModal();
    }
});

// Close modal on Escape key
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        closeCancelModal();
    }
});


// ========================================
// Update UI After Action
// ========================================
function updateAppointmentUI(appointmentId, newStatus) {
    var statusIcon = newStatus === 'approved' ? '✅' : '❌';
    var badgeHTML = '<span class="status-badge ' + newStatus + '">' + statusIcon + ' ' + newStatus + '</span>';

    // Update desktop table badge
    var badge = document.getElementById('badge-' + appointmentId);
    if (badge) {
        badge.outerHTML = badgeHTML;
    }

    // Update mobile card badge
    var mobileBadge = document.getElementById('mobile-badge-' + appointmentId);
    if (mobileBadge) {
        mobileBadge.outerHTML = badgeHTML.replace('id="', 'id="mobile-badge-');
    }

    // Update action buttons
    var actionsHTML = '';
    if (newStatus === 'approved') {
        actionsHTML = '<button class="btn-cancel-action" onclick="showCancelModal(' + appointmentId + ', \'Patient\')" title="Cancel">✕ Cancel</button>';
    } else {
        actionsHTML = '<span style="color: var(--color-text-light); font-size: 0.85rem;">No actions</span>';
    }

    // Desktop actions
    var actions = document.getElementById('actions-' + appointmentId);
    if (actions) {
        actions.innerHTML = actionsHTML;
    }

    // Mobile actions
    var mobileActions = document.getElementById('mobile-actions-' + appointmentId);
    if (mobileActions) {
        mobileActions.innerHTML = actionsHTML;
    }
}


// ========================================
// Refresh Stats via API
// ========================================
function refreshStats() {
    fetch('/admin/api/stats')
        .then(function (response) { return response.json(); })
        .then(function (stats) {
            var counters = document.querySelectorAll('.stat-counter');
            var keys = ['total', 'pending', 'approved', 'cancelled'];
            counters.forEach(function (counter, index) {
                if (keys[index] !== undefined) {
                    var newTarget = stats[keys[index]];
                    counter.dataset.target = newTarget;
                    counter.textContent = newTarget;
                }
            });
        })
        .catch(function (err) {
            console.error('Stats refresh failed:', err);
        });
}


// ========================================
// Toast Notification
// ========================================
function showToast(message, type) {
    type = type || 'info';

    // Create or get flash container
    var container = document.getElementById('flashMessages');
    if (!container) {
        container = document.createElement('div');
        container.className = 'flash-messages';
        container.id = 'flashMessages';
        document.body.appendChild(container);
    }

    var toast = document.createElement('div');
    toast.className = 'flash flash-' + type;
    toast.textContent = message;
    toast.style.cursor = 'pointer';
    toast.onclick = function () { toast.remove(); };

    container.appendChild(toast);

    // Auto-dismiss
    setTimeout(function () {
        toast.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(40px)';
        setTimeout(function () { toast.remove(); }, 300);
    }, 4000);
}
