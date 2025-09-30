// =============================================================================
// SUBLY LANDING PAGE JAVASCRIPT
// =============================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    // initParticles(); // Removed - using global particle system
    initSlideshow();
    initCounterAnimations();
    initScrollAnimations();
    initSolutionAnimation();
    initNavbarScroll();
});

// =============================================================================
// SLIDESHOW SYSTEM
// =============================================================================

let currentSlide = 1;
const totalSlides = 3;
let slideInterval;

function initSlideshow() {
    // Check if slideshow exists before initializing
    const slideshow = document.querySelector('.slideshow-container');
    if (!slideshow) {
        return; // No slideshow present, exit early
    }
    
    // Auto-advance slides every 8 seconds
    slideInterval = setInterval(() => {
        changeSlide(1);
    }, 8000);
    
    // Pause auto-advance on hover
    slideshow.addEventListener('mouseenter', () => {
        clearInterval(slideInterval);
    });
    
    slideshow.addEventListener('mouseleave', () => {
        slideInterval = setInterval(() => {
            changeSlide(1);
        }, 8000);
    });
}

function changeSlide(direction) {
    // Check if slideshow exists before trying to change slides
    const slides = document.querySelectorAll('.slide');
    if (slides.length === 0) {
        return; // No slideshow present, exit early
    }
    
    const newSlide = currentSlide + direction;
    
    if (newSlide < 1) {
        goToSlide(totalSlides);
    } else if (newSlide > totalSlides) {
        goToSlide(1);
    } else {
        goToSlide(newSlide);
    }
}

function goToSlide(slideNumber) {
    // Check if slideshow elements exist before trying to access them
    const activeSlide = document.querySelector('.slide.active');
    const activeIndicator = document.querySelector('.indicator.active');
    const targetSlide = document.querySelector(`[data-slide="${slideNumber}"]`);
    const targetIndicator = document.querySelector(`.indicator[data-slide="${slideNumber}"]`);
    
    // Only proceed if slideshow elements exist
    if (activeSlide && activeIndicator && targetSlide && targetIndicator) {
        // Remove active class from current slide and indicator
        activeSlide.classList.remove('active');
        activeIndicator.classList.remove('active');
        
        // Add active class to new slide and indicator
        targetSlide.classList.add('active');
        targetIndicator.classList.add('active');
        
        currentSlide = slideNumber;
        
        // Restart auto-advance timer
        clearInterval(slideInterval);
        slideInterval = setInterval(() => {
            changeSlide(1);
        }, 8000);
    }
}

// Make functions globally available
window.changeSlide = changeSlide;
window.goToSlide = goToSlide;

// =============================================================================
// PARTICLE SYSTEM - REMOVED
// =============================================================================
// Using global particle system from particles.js instead

// =============================================================================
// COUNTER ANIMATIONS
// =============================================================================

function initCounterAnimations() {
    const counters = document.querySelectorAll('.stat-number, .benefit-number');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });
    
    counters.forEach(counter => {
        observer.observe(counter);
    });
}

function animateCounter(element) {
    const target = parseInt(element.getAttribute('data-target')) || parseInt(element.textContent);
    const duration = 2000; // 2 seconds
    const increment = target / (duration / 16); // 60fps
    let current = 0;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        
        // Format number based on target
        if (target >= 1000) {
            element.textContent = Math.floor(current).toLocaleString('cs-CZ');
        } else if (target < 1) {
            element.textContent = (current / 100).toFixed(1);
        } else {
            element.textContent = Math.floor(current);
        }
    }, 16);
}

// =============================================================================
// SCROLL ANIMATIONS
// =============================================================================

function initScrollAnimations() {
    const animatedElements = document.querySelectorAll('.feature-card, .problem-item, .testimonial-card, .benefit-item');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });
    
    animatedElements.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(30px)';
        element.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(element);
    });
}

// =============================================================================
// SOLUTION ANIMATION
// =============================================================================

function initSolutionAnimation() {
    const steps = document.querySelectorAll('.animation-step');
    if (steps.length === 0) return;
    
    let currentStep = 0;
    
    function showNextStep() {
        // Remove active class from all steps
        steps.forEach(step => step.classList.remove('active'));
        
        // Add active class to current step
        steps[currentStep].classList.add('active');
        
        // Move to next step
        currentStep = (currentStep + 1) % steps.length;
    }
    
    // Start animation
    showNextStep();
    
    // Change step every 3 seconds
    setInterval(showNextStep, 3000);
}

// =============================================================================
// NAVBAR SCROLL EFFECT
// =============================================================================

function initNavbarScroll() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;
    
    // Keep navbar glass effect consistent - no changes on scroll
    // The glass effect is already defined in CSS and should remain constant
}

// =============================================================================
// SMOOTH SCROLLING FOR ANCHOR LINKS
// =============================================================================

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// =============================================================================
// CHART ANIMATION
// =============================================================================

function animateChartBars() {
    const bars = document.querySelectorAll('.chart-bar');
    bars.forEach((bar, index) => {
        setTimeout(() => {
            bar.style.animation = `growUp 1s ease-out forwards`;
        }, index * 200);
    });
}

// Start chart animation when hero section is visible
const heroObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            setTimeout(animateChartBars, 1000);
            heroObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.5 });

const heroVisual = document.querySelector('.hero-visual');
if (heroVisual) {
    heroObserver.observe(heroVisual);
}

// =============================================================================
// MOBILE MENU (if needed in future)
// =============================================================================

function initMobileMenu() {
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    const mobileMenu = document.querySelector('.mobile-menu');
    
    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', () => {
            mobileMenu.classList.toggle('active');
        });
    }
}

// =============================================================================
// PERFORMANCE OPTIMIZATIONS
// =============================================================================

// Throttle scroll events
function throttle(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Debounce resize events
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// =============================================================================
// ERROR HANDLING
// =============================================================================

window.addEventListener('error', function(e) {
    console.error('Landing page error:', e.error);
});

// =============================================================================
// ANALYTICS (placeholder for future implementation)
// =============================================================================

function trackEvent(eventName, properties = {}) {
    // Placeholder for analytics tracking
    console.log('Event tracked:', eventName, properties);
}

// Track CTA clicks
document.querySelectorAll('.cta-primary, .cta-secondary, .demo-btn').forEach(button => {
    button.addEventListener('click', function() {
        const buttonText = this.textContent.trim();
        trackEvent('cta_click', { button_text: buttonText });
    });
});

// Track section views
const sectionObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const sectionName = entry.target.className.split(' ')[0];
            trackEvent('section_view', { section: sectionName });
        }
    });
}, { threshold: 0.5 });

document.querySelectorAll('section').forEach(section => {
    sectionObserver.observe(section);
});
