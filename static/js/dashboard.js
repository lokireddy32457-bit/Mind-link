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
        const cancelModal = document.getElementById('cancelModal');
        const bulkModal = document.getElementById('bulkCancelModal');
        const anyOpen = (cancelModal && cancelModal.classList.contains('active'))
                     || (bulkModal && bulkModal.classList.contains('active'));
        if (!anyOpen) {
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
        closeBulkCancelModal();
        closeSettingsModal();
    }
});


// ========================================
// Bulk Cancel by Date
// ========================================
function showBulkCancelModal() {
    var dateInput = document.getElementById('bulkCancelDate');
    var date = dateInput ? dateInput.value : '';

    if (!date) {
        showToast('⚠️ Please select a date first.', 'error');
        if (dateInput) dateInput.focus();
        return;
    }

    // Format date nicely for the modal
    var parts = date.split('-');
    var friendly = parts[2] + '/' + parts[1] + '/' + parts[0]; // DD/MM/YYYY
    var display = document.getElementById('bulkCancelDateDisplay');
    if (display) display.textContent = friendly;

    document.getElementById('bulkCancelModal').classList.add('active');

    document.getElementById('confirmBulkCancelBtn').onclick = function () {
        closeBulkCancelModal();
        executeBulkCancel(date);
    };
}

function closeBulkCancelModal() {
    var modal = document.getElementById('bulkCancelModal');
    if (modal) modal.classList.remove('active');
}

function executeBulkCancel(date) {
    var btn = document.getElementById('bulkCancelBtn');
    if (btn) {
        btn.disabled = true;
        btn.textContent = '⏳ Cancelling...';
    }

    fetch('/admin/appointments/cancel-by-date', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ date: date })
    })
    .then(function (response) { return response.json(); })
    .then(function (data) {
        if (data.success) {
            showToast('🗑️ ' + data.message, data.count > 0 ? 'success' : 'info');
            // Reload after a short delay so the user can read the toast
            setTimeout(function () { location.reload(); }, 1800);
        } else {
            showToast('❌ ' + data.message, 'error');
        }
    })
    .catch(function (err) {
        console.error('Bulk cancel error:', err);
        showToast('❌ An error occurred. Please try again.', 'error');
    })
    .finally(function () {
        if (btn) {
            btn.disabled = false;
            btn.textContent = '🗑️ Cancel Day';
        }
    });
}

// Close bulk modal on overlay click
document.addEventListener('click', function (e) {
    if (e.target.id === 'bulkCancelModal') {
        closeBulkCancelModal();
    }
    if (e.target.id === 'settingsModal') {
        closeSettingsModal();
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


// ========================================
// Clinic Settings Modal
// ========================================
function openSettingsModal() {
    document.getElementById('settingsModal').classList.add('active');
    document.getElementById('settingsSiteName').focus();
}

function closeSettingsModal() {
    var modal = document.getElementById('settingsModal');
    if (modal) modal.classList.remove('active');
}

function saveSettings() {
    var nameInput = document.getElementById('settingsSiteName');
    var locationInput = document.getElementById('settingsSiteLocation');
    var saveBtn = document.getElementById('saveSettingsBtn');

    var siteName = nameInput ? nameInput.value.trim() : '';
    var siteLocation = locationInput ? locationInput.value.trim() : '';

    if (!siteName) {
        showToast('⚠️ Clinic name cannot be empty.', 'error');
        if (nameInput) nameInput.focus();
        return;
    }
    if (!siteLocation) {
        showToast('⚠️ Location cannot be empty.', 'error');
        if (locationInput) locationInput.focus();
        return;
    }

    if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.textContent = '⏳ Saving...';
    }

    fetch('/admin/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            site_name: siteName,
            site_location: siteLocation
        })
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
        if (data.success) {
            showToast('✅ ' + data.message, 'success');
            closeSettingsModal();
        } else {
            showToast('❌ ' + data.message, 'error');
        }
    })
    .catch(function (err) {
        console.error('Settings save error:', err);
        showToast('❌ An error occurred. Please try again.', 'error');
    })
    .finally(function () {
        if (saveBtn) {
            saveBtn.disabled = false;
            saveBtn.textContent = '💾 Save Changes';
        }
    });
}
