/**
 * Toast Notification System v3
 * Modern, clean toast notifications with icons and titles
 */

class ToastSystem {
    constructor() {
        this.container = null;
        this.toasts = new Map();
        this.init();
    }

    init() {
        // Create toast container if it doesn't exist
        if (!document.querySelector('.toast-container')) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        } else {
            this.container = document.querySelector('.toast-container');
        }

        // Handle URL parameters for flash messages
        this.handleURLFlashMessages();
    }

    /**
     * Show a toast notification
     * @param {string} message - The message to display
     * @param {string} type - success, error, warning, info
     * @param {number} duration - Duration in milliseconds (default: 4000)
     */
    show(message, type = 'info', duration = 4000) {
        const toastId = Date.now() + Math.random();
        const toast = this.createToast(message, type, toastId);
        
        this.container.appendChild(toast);
        this.toasts.set(toastId, toast);

        // Trigger show animation
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });

        // Auto-hide after duration
        if (duration > 0) {
            this.autoHide(toastId, duration);
        }

        return toastId;
    }

    /**
     * Create toast element
     */
    createToast(message, type, id) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.dataset.toastId = id;
        
        // Create icon
        const icon = document.createElement('div');
        icon.className = 'toast-icon';

        // Create content container
        const content = document.createElement('div');
        content.className = 'toast-content';

        // Create title and message
        const title = document.createElement('div');
        title.className = 'toast-title';
        title.textContent = this.getTypeTitle(type);

        const messageDiv = document.createElement('div');
        messageDiv.className = 'toast-message';
        messageDiv.textContent = message;

        // Create progress bar
        const progressBar = document.createElement('div');
        progressBar.className = 'toast-progress';

        // Assemble toast
        content.appendChild(title);
        content.appendChild(messageDiv);
        toast.appendChild(icon);
        toast.appendChild(content);
        toast.appendChild(progressBar);

        return toast;
    }

    /**
     * Get title for toast type
     */
    getTypeTitle(type) {
        const titles = {
            'success': 'Úspěch',
            'error': 'Chyba',
            'warning': 'Varování',
            'info': 'Informace'
        };
        return titles[type] || 'Informace';
    }

    /**
     * Hide a specific toast
     */
    hide(toastId) {
        const toast = this.toasts.get(toastId);
        if (!toast) return;

        toast.classList.add('hide');
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
            this.toasts.delete(toastId);
        }, 300);
    }

    /**
     * Hide all toasts
     */
    hideAll() {
        this.toasts.forEach((toast, id) => {
            this.hide(id);
        });
    }

    /**
     * Auto-hide toast with progress bar
     */
    autoHide(toastId, duration) {
        const toast = this.toasts.get(toastId);
        if (!toast) return;

        const progressBar = toast.querySelector('.toast-progress');
        if (progressBar) {
            progressBar.style.width = '100%';
            progressBar.style.transition = `width ${duration}ms linear`;
            
            setTimeout(() => {
                progressBar.style.width = '0%';
            }, 50);
        }

        setTimeout(() => {
            this.hide(toastId);
        }, duration);
    }

    /**
     * Handle flash messages from URL parameters
     */
    handleURLFlashMessages() {
        const urlParams = new URLSearchParams(window.location.search);
        const flashMessage = urlParams.get('flash');
        const flashType = urlParams.get('type') || 'info';

        if (flashMessage) {
            // Decode the message
            const decodedMessage = decodeURIComponent(flashMessage);
            
            // Show toast
            this.show(decodedMessage, flashType);

            // Clean URL
            const newUrl = new URL(window.location);
            newUrl.searchParams.delete('flash');
            newUrl.searchParams.delete('type');
            window.history.replaceState({}, '', newUrl);
        }
    }

    /**
     * Success toast
     */
    success(message, duration = 4000) {
        return this.show(message, 'success', duration);
    }

    /**
     * Error toast
     */
    error(message, duration = 6000) {
        return this.show(message, 'error', duration);
    }

    /**
     * Warning toast
     */
    warning(message, duration = 5000) {
        return this.show(message, 'warning', duration);
    }

    /**
     * Info toast
     */
    info(message, duration = 4000) {
        return this.show(message, 'info', duration);
    }
}

// Initialize toast system when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.toast = new ToastSystem();
    
    // Override native alert function
    window.alert = function(message) {
        window.toast.warning(message);
    };
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ToastSystem;
}
