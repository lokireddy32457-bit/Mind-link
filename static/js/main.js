/**
 * Mind Link — Main JavaScript
 * Handles navigation, form validation, scroll animations, testimonials, and FAQ accordion.
 */

document.addEventListener('DOMContentLoaded', function () {

    // ========================================
    // Sticky Navigation Shadow
    // ========================================
    const navbar = document.getElementById('navbar');
    if (navbar) {
        window.addEventListener('scroll', function () {
            if (window.scrollY > 20) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        }, { passive: true });
    }

    // ========================================
    // Mobile Hamburger Menu
    // ========================================
    const hamburger = document.getElementById('navHamburger');
    const navLinks = document.getElementById('navLinks');

    if (hamburger && navLinks) {
        hamburger.addEventListener('click', function () {
            hamburger.classList.toggle('active');
            navLinks.classList.toggle('open');
        });

        // Close menu when a link is clicked
        navLinks.querySelectorAll('a').forEach(function (link) {
            link.addEventListener('click', function () {
                hamburger.classList.remove('active');
                navLinks.classList.remove('open');
            });
        });

        // Close menu when clicking outside
        document.addEventListener('click', function (e) {
            if (!navbar.contains(e.target)) {
                hamburger.classList.remove('active');
                navLinks.classList.remove('open');
            }
        });
    }

    // ========================================
    // Scroll Reveal Animations
    // ========================================
    const revealElements = document.querySelectorAll('.reveal');
    if (revealElements.length > 0 && 'IntersectionObserver' in window) {
        const revealObserver = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    revealObserver.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.12,
            rootMargin: '0px 0px -40px 0px'
        });

        revealElements.forEach(function (el) {
            revealObserver.observe(el);
        });
    } else {
        // Fallback: show everything immediately
        revealElements.forEach(function (el) {
            el.classList.add('visible');
        });
    }

    // ========================================
    // Google Reviews Carousel
    // ========================================
    const reviewsCarousel = document.getElementById('reviewsCarousel');
    if (reviewsCarousel) {
        const track = document.getElementById('reviewsTrack');
        const prevBtn = document.getElementById('reviewsPrev');
        const nextBtn = document.getElementById('reviewsNext');
        const cards = track.querySelectorAll('.review-card');
        let currentIndex = 0;
        let autoInterval;

        function getVisibleCount() {
            var w = window.innerWidth;
            if (w < 576) return 1;
            if (w < 992) return 2;
            return 3;
        }

        function getMaxIndex() {
            return Math.max(0, cards.length - getVisibleCount());
        }

        function updateCarousel() {
            var visibleCount = getVisibleCount();
            var gap = parseFloat(getComputedStyle(track).gap) || 24;
            var cardWidth = cards[0].offsetWidth;
            var offset = currentIndex * (cardWidth + gap);
            track.style.transform = 'translateX(-' + offset + 'px)';

            prevBtn.disabled = currentIndex <= 0;
            nextBtn.disabled = currentIndex >= getMaxIndex();
        }

        function goNext() {
            if (currentIndex < getMaxIndex()) {
                currentIndex++;
                updateCarousel();
            } else {
                // Loop back to start
                currentIndex = 0;
                updateCarousel();
            }
        }

        function goPrev() {
            if (currentIndex > 0) {
                currentIndex--;
                updateCarousel();
            }
        }

        function startAuto() {
            autoInterval = setInterval(goNext, 4000);
        }

        function stopAuto() {
            clearInterval(autoInterval);
        }

        prevBtn.addEventListener('click', function () {
            stopAuto();
            goPrev();
            startAuto();
        });

        nextBtn.addEventListener('click', function () {
            stopAuto();
            goNext();
            startAuto();
        });

        reviewsCarousel.addEventListener('mouseenter', stopAuto);
        reviewsCarousel.addEventListener('mouseleave', startAuto);

        // Touch swipe
        var rTouchStartX = 0;
        track.addEventListener('touchstart', function (e) {
            rTouchStartX = e.changedTouches[0].screenX;
            stopAuto();
        }, { passive: true });

        track.addEventListener('touchend', function (e) {
            var diff = rTouchStartX - e.changedTouches[0].screenX;
            if (Math.abs(diff) > 50) {
                if (diff > 0) goNext();
                else goPrev();
            }
            startAuto();
        }, { passive: true });

        // Recalculate on resize
        window.addEventListener('resize', function () {
            if (currentIndex > getMaxIndex()) currentIndex = getMaxIndex();
            updateCarousel();
        });

        updateCarousel();
        startAuto();
    }

    // ========================================
    // FAQ Accordion
    // ========================================
    const faqQuestions = document.querySelectorAll('.faq-question');
    faqQuestions.forEach(function (question) {
        question.addEventListener('click', function () {
            const item = this.parentElement;
            const isOpen = item.classList.contains('open');

            // Close all other items
            document.querySelectorAll('.faq-item.open').forEach(function (openItem) {
                openItem.classList.remove('open');
            });

            // Toggle current item
            if (!isOpen) {
                item.classList.add('open');
            }
        });
    });

    // ========================================
    // Form Validation
    // ========================================

    // Validators
    function isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    function isValidPhone(phone) {
        // Must contain exactly 10 digits
        var digits = phone.replace(/\D/g, '');
        return digits.length === 10;
    }

    // Restrict phone input to only allow digits and max length of 10
    var phoneInput = document.getElementById('phone');
    if (phoneInput) {
        phoneInput.addEventListener('input', function () {
            this.value = this.value.replace(/\D/g, '').substring(0, 10);
        });
    }

    function isFutureDate(dateStr) {
        if (!dateStr) return false;
        var today = new Date();
        today.setHours(0, 0, 0, 0);
        var selected = new Date(dateStr + 'T00:00:00');
        return selected >= today;
    }

    function showError(input, show) {
        var group = input.closest('.form-group');
        if (!group) return;
        if (show) {
            group.classList.add('has-error');
            input.classList.add('error');
        } else {
            group.classList.remove('has-error');
            input.classList.remove('error');
        }
    }

    // Booking Form Validation
    var bookingForm = document.getElementById('bookingForm');
    if (bookingForm) {
        // Set min date to today
        var dateInput = document.getElementById('preferred_date');
        if (dateInput) {
            var today = new Date().toISOString().split('T')[0];
            dateInput.setAttribute('min', today);
        }

        // Real-time validation on blur
        var fields = bookingForm.querySelectorAll('input, select, textarea');
        fields.forEach(function (field) {
            field.addEventListener('blur', function () {
                validateBookingField(this);
            });
            field.addEventListener('input', function () {
                if (this.closest('.form-group').classList.contains('has-error')) {
                    validateBookingField(this);
                }
            });
        });

        function validateBookingField(field) {
            var id = field.id;
            var value = field.value.trim();

            switch (id) {
                case 'name':
                    showError(field, value.length < 2);
                    return value.length >= 2;
                case 'email':
                    showError(field, !isValidEmail(value));
                    return isValidEmail(value);
                case 'phone':
                    showError(field, !isValidPhone(value));
                    return isValidPhone(value);
                case 'service_type':
                    showError(field, !value);
                    return !!value;
                case 'preferred_date':
                    showError(field, !isFutureDate(value));
                    return isFutureDate(value);
                case 'preferred_time':
                    showError(field, !value);
                    return !!value;
                default:
                    return true;
            }
        }

        bookingForm.addEventListener('submit', function (e) {
            var isValid = true;
            var requiredIds = ['name', 'email', 'phone', 'service_type', 'preferred_date', 'preferred_time'];

            requiredIds.forEach(function (id) {
                var field = document.getElementById(id);
                if (field && !validateBookingField(field)) {
                    isValid = false;
                }
            });

            if (!isValid) {
                e.preventDefault();
                // Scroll to first error
                var firstError = bookingForm.querySelector('.has-error');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                return;
            }

            // ── EmailJS Integration ──
            // If sendAppointmentEmail is available, send the email before form submission
            if (typeof sendAppointmentEmail === 'function') {
                e.preventDefault();

                var submitBtn = bookingForm.querySelector('button[type="submit"]');
                var originalText = submitBtn.textContent;
                submitBtn.disabled = true;
                submitBtn.textContent = '📧 Sending notification...';
                submitBtn.style.opacity = '0.7';

                sendAppointmentEmail(bookingForm)
                    .then(function () {
                        // Restore button and submit form normally to the server
                        submitBtn.textContent = '✅ Submitting...';
                        bookingForm.submit();
                    })
                    .catch(function () {
                        // Even if email fails, still submit the form to the server
                        submitBtn.textContent = originalText;
                        submitBtn.disabled = false;
                        submitBtn.style.opacity = '1';
                        bookingForm.submit();
                    });
            }
        });
    }

    // Contact Form Validation
    var contactForm = document.getElementById('contactForm');
    if (contactForm) {
        var contactFields = contactForm.querySelectorAll('input, textarea');
        contactFields.forEach(function (field) {
            field.addEventListener('blur', function () {
                validateContactField(this);
            });
            field.addEventListener('input', function () {
                if (this.closest('.form-group').classList.contains('has-error')) {
                    validateContactField(this);
                }
            });
        });

        function validateContactField(field) {
            var id = field.id;
            var value = field.value.trim();

            switch (id) {
                case 'contact_name':
                    showError(field, value.length < 2);
                    return value.length >= 2;
                case 'contact_email':
                    showError(field, !isValidEmail(value));
                    return isValidEmail(value);
                case 'contact_subject':
                    showError(field, value.length < 2);
                    return value.length >= 2;
                case 'contact_message':
                    showError(field, value.length < 10);
                    return value.length >= 10;
                default:
                    return true;
            }
        }

        contactForm.addEventListener('submit', function (e) {
            var isValid = true;
            var requiredIds = ['contact_name', 'contact_email', 'contact_subject', 'contact_message'];

            requiredIds.forEach(function (id) {
                var field = document.getElementById(id);
                if (field && !validateContactField(field)) {
                    isValid = false;
                }
            });

            if (!isValid) {
                e.preventDefault();
                var firstError = contactForm.querySelector('.has-error');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        });
    }

    // ========================================
    // Smooth Scroll for Anchor Links
    // ========================================
    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
        anchor.addEventListener('click', function (e) {
            var targetId = this.getAttribute('href');
            if (targetId === '#') return;
            var target = document.querySelector(targetId);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // ========================================
    // Auto-dismiss Flash Messages
    // ========================================
    var flashes = document.querySelectorAll('.flash');
    flashes.forEach(function (flash) {
        setTimeout(function () {
            flash.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            flash.style.opacity = '0';
            flash.style.transform = 'translateX(40px)';
            setTimeout(function () { flash.remove(); }, 300);
        }, 5000);
    });

});
