// FoodRescue Platform Main JavaScript

document.addEventListener('DOMContentLoaded', function () {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 6000);
    });

    // Mark notification as read via AJAX
    const markReadButtons = document.querySelectorAll('.btn-mark-notification-read');
    markReadButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault();
            const notificationId = this.getAttribute('data-notification-id');
            const targetItem = document.getElementById(`notification-item-${notificationId}`);
            
            fetch(`/notifications/mark-read/${notificationId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (targetItem) {
                        targetItem.classList.remove('bg-light');
                        targetItem.classList.add('opacity-75');
                    }
                    button.remove();
                    // Update badge count
                    const badge = document.getElementById('navbar-notification-badge');
                    if (badge) {
                        const current = parseInt(badge.innerText, 10);
                        if (current > 1) {
                            badge.innerText = current - 1;
                        } else {
                            badge.remove();
                        }
                    }
                }
            })
            .catch(err => console.error('Error marking notification read:', err));
        });
    });
});

// Helper: Get Cookie for CSRF Token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    if (!cookieValue && name === 'csrftoken') {
        const globalEl = document.getElementById('global-csrf-token');
        if (globalEl) cookieValue = globalEl.value;
    }
    return cookieValue;
}
