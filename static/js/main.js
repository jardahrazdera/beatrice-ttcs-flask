/**
 * Main JavaScript file for common functionality
 */

// Utility function for formatting temperature
function formatTemperature(temp) {
    if (temp === null || temp === undefined) {
        return '--';
    }
    return temp.toFixed(1);
}

// Utility function for updating element text
function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

// Utility function for toggling element visibility
function toggleElement(id, show) {
    const element = document.getElementById(id);
    if (element) {
        element.style.display = show ? 'block' : 'none';
    }
}

// Utility function for adding CSS class
function addClass(id, className) {
    const element = document.getElementById(id);
    if (element) {
        element.classList.add(className);
    }
}

// Utility function for removing CSS class
function removeClass(id, className) {
    const element = document.getElementById(id);
    if (element) {
        element.classList.remove(className);
    }
}

// Show notification message
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} notification-toast`;
    notification.textContent = message;
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '1000';
    notification.style.minWidth = '300px';

    document.body.appendChild(notification);

    // Auto-remove after 5 seconds with fade out
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(400px)';
        notification.style.transition = 'all 0.3s ease-out';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 5000);
}

// API call helper
async function apiCall(url, method = 'GET', data = null) {
    try {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            }
        };

        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(url, options);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API call error:', error);
        throw error;
    }
}

/**
 * Handle logout - disable manual mode before logging out
 */
async function handleLogout() {
    // Check if manual override password exists (section is unlocked)
    const manualPassword = sessionStorage.getItem('manualOverridePassword');

    if (manualPassword) {
        try {
            // Disable manual mode before logout
            await apiCall('/api/settings/manual', 'POST', {
                manual_override: false,
                manual_heating: false,
                manual_pump: false,
                super_admin_password: manualPassword
            });
        } catch (error) {
            console.error('Error disabling manual mode on logout:', error);
            // Continue with logout even if this fails
        }
    }

    // Clear all session storage
    sessionStorage.clear();

    // Allow navigation to logout
    return true;
}

// Export utilities for use in other files
window.utils = {
    formatTemperature,
    updateElement,
    toggleElement,
    addClass,
    removeClass,
    showNotification,
    apiCall
};

// Export handleLogout globally
window.handleLogout = handleLogout;
