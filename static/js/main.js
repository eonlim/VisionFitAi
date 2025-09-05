/**
 * VisionFit AI - Main JavaScript
 * Common functionality and utilities
 */

// Global app namespace
window.VisionFit = {
    // App configuration
    config: {
        apiBase: '/api',
        animationDuration: 300,
        debounceDelay: 500
    },

    // Utility functions
    utils: {},

    // Component modules
    components: {},

    // API helpers
    api: {}
};

// Utility Functions
VisionFit.utils = {
    /**
     * Debounce function calls
     */
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Format numbers with locale-specific formatting
     */
    formatNumber: function(number) {
        return new Intl.NumberFormat().format(number);
    },

    /**
     * Format duration in minutes to human-readable format
     */
    formatDuration: function(minutes) {
        if (minutes < 60) {
            return `${minutes} min`;
        }
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
    },

    /**
     * Format date to readable string
     */
    formatDate: function(date) {
        return new Date(date).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    },

    /**
     * Show toast notification
     */
    showToast: function(message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';

        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(toast);

        // Auto remove after duration
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, duration);
    },

    /**
     * Show loading spinner
     */
    showLoader: function(element, text = 'Loading...') {
        const loader = document.createElement('div');
        loader.className = 'text-center py-4 loader-overlay';
        loader.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2 text-muted">${text}</p>
        `;

        element.style.position = 'relative';
        element.appendChild(loader);
        return loader;
    },

    /**
     * Hide loading spinner
     */
    hideLoader: function(element) {
        const loader = element.querySelector('.loader-overlay');
        if (loader) {
            loader.remove();
        }
    },

    /**
     * Animate counter numbers
     */
    animateCounter: function(element, target, duration = 2000) {
        const start = parseInt(element.textContent) || 0;
        const increment = (target - start) / (duration / 16);
        let current = start;

        const timer = setInterval(() => {
            current += increment;
            element.textContent = Math.floor(current).toLocaleString();

            if ((increment > 0 && current >= target) || (increment < 0 && current <= target)) {
                element.textContent = target.toLocaleString();
                clearInterval(timer);
            }
        }, 16);
    },

    /**
     * Smooth scroll to element
     */
    scrollTo: function(element, offset = 80) {
        const elementPosition = element.offsetTop - offset;
        window.scrollTo({
            top: elementPosition,
            behavior: 'smooth'
        });
    },

    /**
     * Check if element is in viewport
     */
    isInViewport: function(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    },

    /**
     * Local storage helpers
     */
    storage: {
        set: function(key, value) {
            try {
                localStorage.setItem(`visionfit_${key}`, JSON.stringify(value));
            } catch (e) {
                console.error('Failed to save to localStorage:', e);
            }
        },

        get: function(key) {
            try {
                const item = localStorage.getItem(`visionfit_${key}`);
                return item ? JSON.parse(item) : null;
            } catch (e) {
                console.error('Failed to read from localStorage:', e);
                return null;
            }
        },

        remove: function(key) {
            localStorage.removeItem(`visionfit_${key}`);
        }
    }
};

// API Helper Functions
VisionFit.api = {
    /**
     * Generic API request handler
     */
    request: async function(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        };

        const config = { ...defaultOptions, ...options };

        try {
            const response = await fetch(`${VisionFit.config.apiBase}${endpoint}`, config);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }

            return await response.text();
        } catch (error) {
            console.error('API request failed:', error);
            VisionFit.utils.showToast('Network error. Please try again.', 'danger');
            throw error;
        }
    },

    /**
     * GET request
     */
    get: function(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },

    /**
     * POST request
     */
    post: function(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    /**
     * PUT request
     */
    put: function(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    /**
     * DELETE request
     */
    delete: function(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
};

// Component: Form Validation
VisionFit.components.formValidation = {
    init: function() {
        const forms = document.querySelectorAll('form[data-validate]');
        forms.forEach(form => this.attachValidation(form));
    },

    attachValidation: function(form) {
        const inputs = form.querySelectorAll('input, select, textarea');

        inputs.forEach(input => {
            input.addEventListener('blur', () => this.validateField(input));
            input.addEventListener('input', () => this.clearErrors(input));
        });

        form.addEventListener('submit', (e) => {
            if (!this.validateForm(form)) {
                e.preventDefault();
            }
        });
    },

    validateField: function(field) {
        const value = field.value.trim();
        let isValid = true;
        let errorMessage = '';

        // Required validation
        if (field.hasAttribute('required') && !value) {
            isValid = false;
            errorMessage = 'This field is required';
        }

        // Email validation
        if (field.type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                errorMessage = 'Please enter a valid email address';
            }
        }

        // Password validation
        if (field.type === 'password' && value) {
            if (value.length < 6) {
                isValid = false;
                errorMessage = 'Password must be at least 6 characters';
            }
        }

        // Custom validation patterns
        if (field.hasAttribute('pattern') && value) {
            const pattern = new RegExp(field.getAttribute('pattern'));
            if (!pattern.test(value)) {
                isValid = false;
                errorMessage = field.getAttribute('data-error') || 'Invalid format';
            }
        }

        this.showFieldError(field, isValid, errorMessage);
        return isValid;
    },

    validateForm: function(form) {
        const inputs = form.querySelectorAll('input, select, textarea');
        let isFormValid = true;

        inputs.forEach(input => {
            if (!this.validateField(input)) {
                isFormValid = false;
            }
        });

        return isFormValid;
    },

    showFieldError: function(field, isValid, message) {
        const errorElement = field.parentNode.querySelector('.error-message');

        if (isValid) {
            field.classList.remove('is-invalid');
            if (errorElement) {
                errorElement.remove();
            }
        } else {
            field.classList.add('is-invalid');

            if (!errorElement) {
                const error = document.createElement('div');
                error.className = 'error-message text-danger small mt-1';
                error.textContent = message;
                field.parentNode.appendChild(error);
            } else {
                errorElement.textContent = message;
            }
        }
    },

    clearErrors: function(field) {
        field.classList.remove('is-invalid');
        const errorElement = field.parentNode.querySelector('.error-message');
        if (errorElement) {
            errorElement.remove();
        }
    }
};

// Component: Smooth Animations
VisionFit.components.animations = {
    init: function() {
        this.setupScrollAnimations();
        this.setupHoverEffects();
        this.setupParallax();
    },

    setupScrollAnimations: function() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, observerOptions);

        // Observe elements with animation classes
        document.querySelectorAll('.fade-in-up, .fade-in-left, .fade-in-right').forEach(el => {
            if (el) {
                observer.observe(el);
            }
        });
    },

    setupHoverEffects: function() {
        // 3D card effects
        document.querySelectorAll('.card-3d').forEach(card => {
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;

                const centerX = rect.width / 2;
                const centerY = rect.height / 2;

                const rotateX = (y - centerY) / 10;
                const rotateY = (centerX - x) / 10;

                card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(10px)`;
            });

            card.addEventListener('mouseleave', () => {
                card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateZ(0px)';
            });
        });
    },

    setupParallax: function() {
        const parallaxElements = document.querySelectorAll('.parallax-element');

        if (parallaxElements.length === 0) return;

        const handleScroll = VisionFit.utils.debounce(() => {
            const scrolled = window.pageYOffset;

            parallaxElements.forEach(element => {
                const rate = scrolled * -0.5;
                element.style.transform = `translateY(${rate}px)`;
            });
        }, 10);

        window.addEventListener('scroll', handleScroll);
    }
};

// Component: Timer
VisionFit.components.timer = {
    timers: new Map(),

    start: function(id, callback, interval = 1000) {
        if (this.timers.has(id)) {
            this.stop(id);
        }

        const startTime = Date.now();
        const timer = setInterval(() => {
            const elapsed = Date.now() - startTime;
            callback(Math.floor(elapsed / 1000));
        }, interval);

        this.timers.set(id, { timer, startTime });
    },

    stop: function(id) {
        const timerData = this.timers.get(id);
        if (timerData) {
            clearInterval(timerData.timer);
            this.timers.delete(id);
        }
    },

    getElapsed: function(id) {
        const timerData = this.timers.get(id);
        if (timerData) {
            return Math.floor((Date.now() - timerData.startTime) / 1000);
        }
        return 0;
    },

    formatTime: function(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
};

// Component: Camera Helper
VisionFit.components.camera = {
    stream: null,
    isActive: false,

    async initialize(videoElement, constraints = {}) {
        // Check if browser supports getUserMedia
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            const errorMsg = 'Your browser does not support camera access. Please try a modern browser like Chrome, Firefox, or Edge.';
            console.error(errorMsg);
            VisionFit.utils.showToast(errorMsg, 'danger');
            throw new Error(errorMsg);
        }

        const defaultConstraints = {
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: 'user'
            },
            audio: false
        };

        const finalConstraints = { ...defaultConstraints, ...constraints };
        console.log('Camera constraints:', finalConstraints);

        try {
            console.log('Attempting to access camera...');
            this.stream = await navigator.mediaDevices.getUserMedia(finalConstraints);
            console.log('Camera access granted:', this.stream);

            // Ensure video element exists
            if (!videoElement) {
                throw new Error('Video element not found');
            }

            videoElement.srcObject = this.stream;
            this.isActive = true;

            return new Promise((resolve) => {
                videoElement.onloadedmetadata = () => {
                    console.log('Video metadata loaded');

                    // Fix video orientation and display
                    videoElement.style.transform = 'scaleX(-1)'; // Mirror the video
                    videoElement.style.width = '100%';
                    videoElement.style.height = 'auto';
                    videoElement.style.objectFit = 'cover';

                    // Ensure video is visible
                    videoElement.style.display = 'block';

                    resolve(this.stream);
                };

                // Add a fallback in case onloadedmetadata doesn't fire
                setTimeout(() => {
                    if (this.isActive && this.stream) {
                        console.log('Video metadata timeout - resolving anyway');

                        // Apply orientation fixes even if metadata didn't load
                        videoElement.style.transform = 'scaleX(-1)';
                        videoElement.style.width = '100%';
                        videoElement.style.height = 'auto';
                        videoElement.style.objectFit = 'cover';
                        videoElement.style.display = 'block';

                        resolve(this.stream);
                    }
                }, 1000);
            });
        } catch (error) {
            console.error('Camera initialization failed:', error.name, error.message);
            let errorMsg = 'Failed to access camera. ';

            // Provide more specific error messages
            if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
                errorMsg += 'Please allow camera access in your browser permissions.';
            } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
                errorMsg += 'No camera detected. Please connect a camera and try again.';
            } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
                errorMsg += 'Camera is in use by another application. Please close other apps using the camera.';
            } else if (error.name === 'OverconstrainedError') {
                errorMsg += 'Camera constraints cannot be satisfied. Using default settings.';
                // Try again with minimal constraints
                return this.initialize(videoElement, { video: true, audio: false });
            } else {
                errorMsg += error.message || 'Unknown camera error.';
            }

            VisionFit.utils.showToast(errorMsg, 'danger');
            throw error;
        }
    },

    stop() {
        console.log('Stopping camera...');
        if (this.stream) {
            try {
                const tracks = this.stream.getTracks();
                console.log(`Stopping ${tracks.length} camera tracks`);
                tracks.forEach(track => {
                    try {
                        track.stop();
                        console.log(`Track ${track.id} stopped successfully`);
                    } catch (trackError) {
                        console.error(`Error stopping track ${track.id}:`, trackError);
                    }
                });
            } catch (streamError) {
                console.error('Error accessing stream tracks:', streamError);
            } finally {
                this.stream = null;
                this.isActive = false;
                console.log('Camera stopped and resources cleared');
            }
        } else {
            console.log('No active camera stream to stop');
            this.isActive = false;
        }
    },

    captureFrame(videoElement, canvasElement) {
        if (!this.isActive) return null;

        const context = canvasElement.getContext('2d');
        canvasElement.width = videoElement.videoWidth;
        canvasElement.height = videoElement.videoHeight;

        context.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);

        return {
            canvas: canvasElement,
            dataURL: canvasElement.toDataURL('image/jpeg', 0.8),
            imageData: context.getImageData(0, 0, canvasElement.width, canvasElement.height)
        };
    }
};

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize components
    VisionFit.components.formValidation.init();
    VisionFit.components.animations.init();

    // Setup global event listeners
    setupGlobalEventListeners();

    // Setup navigation enhancements
    setupNavigation();

    // Setup responsive handling
    setupResponsiveHandlers();

    console.log('VisionFit AI initialized successfully');
});

// Global event listeners
function setupGlobalEventListeners() {
    // Handle all form submissions with loading states
    document.addEventListener('submit', function(e) {
        const form = e.target;
        const submitBtn = form.querySelector('button[type="submit"]');

        if (submitBtn && !submitBtn.disabled) {
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
            submitBtn.disabled = true;

            // Re-enable after 5 seconds as fallback
            setTimeout(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }, 5000);
        }
    });

    // Handle flash message auto-hide
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(alert => {
            if (alert.querySelector('.btn-close')) {
                alert.querySelector('.btn-close').click();
            }
        });
    }, 5000);

    // Handle smooth scrolling for anchor links
    document.addEventListener('click', function(e) {
        const link = e.target.closest('a[href^="#"]');
        if (link) {
            e.preventDefault();
            const targetId = link.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);

            if (targetElement) {
                VisionFit.utils.scrollTo(targetElement);
            }
        }
    });
}

// Navigation enhancements
function setupNavigation() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;

    // Navbar scroll effect
    let lastScrollY = window.scrollY;

    window.addEventListener('scroll', VisionFit.utils.debounce(() => {
        const currentScrollY = window.scrollY;

        if (currentScrollY > 100) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }

        // Hide/show navbar on scroll
        if (currentScrollY > lastScrollY && currentScrollY > 200) {
            navbar.style.transform = 'translateY(-100%)';
        } else {
            navbar.style.transform = 'translateY(0)';
        }

        lastScrollY = currentScrollY;
    }, 100));

    // Active nav item highlighting
    const navLinks = navbar.querySelectorAll('.nav-link');
    const currentPath = window.location.pathname;

    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}

// Responsive handlers
function setupResponsiveHandlers() {
    // Handle mobile menu
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');

    if (navbarToggler && navbarCollapse) {
        document.addEventListener('click', function(e) {
            if (!navbarCollapse.contains(e.target) && !navbarToggler.contains(e.target)) {
                const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
                if (bsCollapse && navbarCollapse.classList.contains('show')) {
                    bsCollapse.hide();
                }
            }
        });
    }

    // Handle window resize
    window.addEventListener('resize', VisionFit.utils.debounce(() => {
        // Recalculate any layout-dependent components
        const event = new CustomEvent('visionfit:resize');
        window.dispatchEvent(event);
    }, 250));
}

// Export for global access
window.VisionFit = VisionFit;
