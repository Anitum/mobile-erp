document.addEventListener('DOMContentLoaded', function() {
    // Star rating system
    const ratingContainers = document.querySelectorAll('.rating-container');
    ratingContainers.forEach(container => {
        const stars = container.querySelectorAll('.fas.fa-star');
        const input = container.querySelector('input[type="radio"]');
        
        stars.forEach((star, index) => {
            star.addEventListener('mouseover', () => {
                // Highlight stars on hover
                for (let i = 0; i <= index; i++) {
                    stars[i].style.color = '#ffc107';
                }
            });
            
            star.addEventListener('mouseout', () => {
                // Reset stars if not selected
                stars.forEach(s => {
                    s.style.color = input.checked ? '#ffc107' : '#dee2e6';
                });
            });
        });
    });

    // Image preview
    const photoInputs = document.querySelectorAll('input[type="file"][accept="image/*"]');
    photoInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                if (file.size > 5 * 1024 * 1024) { // 5MB limit
                    alert('File size should not exceed 5MB');
                    e.target.value = '';
                    return;
                }

                const reader = new FileReader();
                reader.onload = function(e) {
                    // Create preview if doesn't exist
                    let preview = input.nextElementSibling;
                    if (!preview || !preview.classList.contains('image-preview')) {
                        preview = document.createElement('div');
                        preview.className = 'image-preview mt-2';
                        preview.style.maxWidth = '200px';
                        input.parentNode.appendChild(preview);
                    }
                    preview.innerHTML = `
                        <img src="${e.target.result}" class="img-fluid rounded" />
                        <button type="button" class="btn btn-sm btn-danger mt-1 remove-preview">
                            Remove
                        </button>
                    `;

                    // Add remove functionality
                    preview.querySelector('.remove-preview').addEventListener('click', () => {
                        input.value = '';
                        preview.remove();
                    });
                };
                reader.readAsDataURL(file);
            }
        });
    });

    // Form validation
    const form = document.querySelector('form');
    form.addEventListener('submit', function(e) {
        let isValid = true;
        const requiredInputs = form.querySelectorAll('[required]');
        
        requiredInputs.forEach(input => {
            if (!input.value) {
                isValid = false;
                input.classList.add('is-invalid');
            } else {
                input.classList.remove('is-invalid');
            }
        });

        if (!isValid) {
            e.preventDefault();
            alert('Please fill in all required fields');
        }
    });

    // Auto-save functionality
    let autoSaveTimeout;
    const autoSaveInputs = form.querySelectorAll('textarea, input[type="text"]');
    autoSaveInputs.forEach(input => {
        input.addEventListener('input', () => {
            clearTimeout(autoSaveTimeout);
            autoSaveTimeout = setTimeout(() => {
                localStorage.setItem('daily_report_draft', JSON.stringify({
                    content: form.querySelector('[name="report_content"]').value,
                    timestamp: new Date().toISOString()
                }));
            }, 1000);
        });
    });

    // Load draft if exists
    const savedDraft = localStorage.getItem('daily_report_draft');
    if (savedDraft) {
        const draft = JSON.parse(savedDraft);
        const draftDate = new Date(draft.timestamp);
        const now = new Date();
        
        // Only load draft if it's from today
        if (draftDate.toDateString() === now.toDateString()) {
            form.querySelector('[name="report_content"]').value = draft.content;
        }
    }
});
