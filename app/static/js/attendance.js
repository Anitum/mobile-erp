document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Handle attendance marking
    const markAttendanceModal = document.getElementById('markAttendanceModal');
    if (markAttendanceModal) {
        markAttendanceModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const userId = button.getAttribute('data-user-id');
            const userName = button.getAttribute('data-user-name');
            const currentStatus = button.getAttribute('data-current-status');
            
            const modalTitle = this.querySelector('.modal-title');
            const userIdInput = this.querySelector('#modalUserId');
            const userNameSpan = this.querySelector('#modalUserName');
            const statusSelect = this.querySelector('select[name="status"]');
            
            modalTitle.textContent = `Mark Attendance - ${userName}`;
            userIdInput.value = userId;
            userNameSpan.textContent = userName;
            
            if (currentStatus) {
                statusSelect.value = currentStatus;
            }
        });
    }

    // Date range picker initialization
    const dateRangePicker = document.querySelector('.date-range-picker');
    if (dateRangePicker) {
        new DateRangePicker(dateRangePicker, {
            showDropdowns: true,
            ranges: {
                'Today': [moment(), moment()],
                'Yesterday': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
                'Last 7 Days': [moment().subtract(6, 'days'), moment()],
                'Last 30 Days': [moment().subtract(29, 'days'), moment()],
                'This Month': [moment().startOf('month'), moment().endOf('month')]
            }
        });
    }

    // Attendance Chart
    const chartCanvas = document.getElementById('attendanceChart');
    if (chartCanvas) {
        const ctx = chartCanvas.getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartLabels,
                datasets: [{
                    label: 'Attendance Rate',
                    data: chartData,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }

    // Bulk attendance marking
    const bulkActionCheckbox = document.querySelector('#bulkActionCheckbox');
    if (bulkActionCheckbox) {
        bulkActionCheckbox.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.user-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateBulkActionButton();
        });

        document.querySelectorAll('.user-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', updateBulkActionButton);
        });
    }

    function updateBulkActionButton() {
        const checkedCount = document.querySelectorAll('.user-checkbox:checked').length;
        const bulkActionBtn = document.querySelector('#bulkActionBtn');
        if (bulkActionBtn) {
            bulkActionBtn.textContent = `Mark Selected (${checkedCount})`;
            bulkActionBtn.disabled = checkedCount === 0;
        }
    }
});

// Export attendance data
function exportAttendance(format) {
    const filters = {
        startDate: document.querySelector('#startDate').value,
        endDate: document.querySelector('#endDate').value,
        role: document.querySelector('#roleFilter').value
    };

    const url = `/admin/attendance/export?format=${format}&` + new URLSearchParams(filters);
    window.location.href = url;
}

// Print attendance report
function printAttendanceReport() {
    window.print();
}
