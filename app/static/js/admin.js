import WeeklyAttendanceChart from '../components/charts/WeeklyAttendanceChart';

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the chart
    const chartContainer = document.getElementById('weeklyAttendanceChart');
    if (chartContainer) {
        ReactDOM.render(
            React.createElement(WeeklyAttendanceChart),
            chartContainer
        );
    }
});

document.addEventListener('DOMContentLoaded', function() {
    // File Upload Preview
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const fileName = e.target.files[0]?.name || 'No file chosen';
            const wrapper = input.closest('.file-upload-wrapper');
            if (wrapper) {
                wrapper.querySelector('.file-upload-text').textContent = fileName;
            }
        });
    });

    // Message Notifications
    function checkNewMessages() {
        fetch('/admin/check-messages')
            .then(response => response.json())
            .then(data => {
                if (data.newMessages > 0) {
                    showNotification(`You have ${data.newMessages} new message(s)`);
                }
            });
    }

    function showNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'alert alert-info alert-dismissible fade show position-fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '1050';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    // Mark Messages as Read
    const messageCards = document.querySelectorAll('.message-card.unread');
    messageCards.forEach(card => {
        card.addEventListener('click', function() {
            const messageId = this.dataset.messageId;
            fetch(`/admin/mark-message-read/${messageId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(() => {
                card.classList.remove('unread');
            });
        });
    });

    // Dynamic Form Validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Date Range Filter
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        input.addEventListener('change', function() {
            const startDate = document.querySelector('input[name="start_date"]').value;
            const endDate = document.querySelector('input[name="end_date"]').value;
            
            if (startDate && endDate) {
                filterReportsByDate(startDate, endDate);
            }
        });
    });

    function filterReportsByDate(startDate, endDate) {
        const reports = document.querySelectorAll('.reports-list .card');
        reports.forEach(report => {
            const reportDate = report.dataset.date;
            if (reportDate >= startDate && reportDate <= endDate) {
                report.style.display = 'block';
            } else {
                report.style.display = 'none';
            }
        });
    }

    // Search Functionality
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const searchableElements = document.querySelectorAll('[data-searchable]');
            
            searchableElements.forEach(element => {
                const text = element.textContent.toLowerCase();
                element.closest('.card').style.display = 
                    text.includes(searchTerm) ? 'block' : 'none';
            });
        }, 300));
    }

    // Debounce Helper Function
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

    // Initialize Tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Check for new messages periodically
    setInterval(checkNewMessages, 30000); // Check every 30 seconds
});
