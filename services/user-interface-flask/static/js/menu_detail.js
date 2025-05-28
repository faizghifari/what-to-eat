document.addEventListener('DOMContentLoaded', function () {
    const stars = document.querySelectorAll('.rating-star');
    const reviewTextArea = document.getElementById('reviewText');
    const submitButton = document.getElementById('submitReview');
    let currentRating = document.querySelector('.rating-star[style*="gold"]')?.dataset.rating || 0;
    let selectedRating = currentRating;

    // Highlight stars on hover
    stars.forEach(star => {
        star.addEventListener('mouseover', function () {
            const rating = this.dataset.rating;
            updateStarDisplay(rating, '#ffd700'); // Hover color
        });

        star.addEventListener('mouseout', function () {
            updateStarDisplay(selectedRating || currentRating, 'gold'); // Reset to selected or current rating
        });

        star.addEventListener('click', function () {
            selectedRating = parseInt(this.dataset.rating);
            updateStarDisplay(selectedRating, 'gold');
        });
    });

    // Handle submit button click
    submitButton.addEventListener('click', function () {
        if (!selectedRating) {
            showAlert('Please select a rating before submitting', 'error');
            return;
        }
        submitReview(selectedRating, reviewTextArea.value);
    });

    function updateStarDisplay(rating, color) {
        stars.forEach(star => {
            const starRating = parseInt(star.dataset.rating);
            star.style.color = starRating <= rating ? color : 'gray';
        });
    }

    function submitReview(rating, review) {
        const menuId = window.location.pathname.split('/').pop();

        fetch(`/api/menu/${menuId}/rate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                rating: rating,
                review: review
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    currentRating = rating;
                    updateStarDisplay(rating, 'gold');
                    // Show success message
                    showAlert('Rating submitted successfully!', 'success');
                } else {
                    showAlert('Failed to submit rating. Please try again.', 'error');
                }
            })
            .catch(error => {
                showAlert('An error occurred. Please try again.', 'error');
                console.error('Error:', error);
            });
    }

    function showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show`;
        alertDiv.role = 'alert';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        const container = document.querySelector('.container');
        container.insertBefore(alertDiv, container.firstChild);

        // Auto dismiss after 3 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 3000);
    }
});
