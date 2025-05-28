// Recipe search functionality
let searchTimeout;

document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.querySelector('.search-bar input');
    if (searchInput) {
        searchInput.addEventListener('input', handleRecipeSearch);
    }

    // Rating functionality
    const ratingButtons = document.querySelectorAll('.recipe-rating button');
    ratingButtons.forEach(button => {
        button.addEventListener('click', handleRating);
    });
});

async function handleRecipeSearch(event) {
    clearTimeout(searchTimeout);
    const query = event.target.value.trim();

    if (query) {
        searchTimeout = setTimeout(async () => {
            const searchModal = new bootstrap.Modal(document.getElementById('searchRecipeModal'));

            try {
                searchModal.show();
                const results = await api.get('/recipe/search?query=' + encodeURIComponent(query));
                if (results.length > 0) {
                    displaySearchResults(results);
                } else {
                    showFlashMessage('No recipes found.', 'info');
                }
            } catch (error) {
                showFlashMessage('Failed to search recipes.', 'danger');
            } finally {
                searchModal.hide();
            }
        }, 1000);
    }
}

function displaySearchResults(recipes) {
    const container = document.querySelector('.recipe-results');
    if (!container) return;

    container.innerHTML = recipes.map(recipe => `
        <div class="col-md-4 mb-4">
            <div class="card recipe-card">
                <img src="${recipe.image_url || 'https://via.placeholder.com/300x200'}" 
                     class="card-img-top" alt="${recipe.name}">
                <div class="card-body">
                    <h5 class="card-title">${recipe.name}</h5>
                    <p class="card-text">
                        <small class="text-muted">
                            <span class="me-3">⏰ ${recipe.cook_time} mins</span>
                            <span>⭐ ${recipe.rating}/5</span>
                        </small>
                    </p>
                    <p class="card-text">${recipe.description}</p>
                    <a href="/recipe/${recipe.id}" class="btn btn-primary">View Recipe</a>
                </div>
            </div>
        </div>
    `).join('');
}

async function handleRating(event) {
    const button = event.currentTarget;
    const recipeId = button.dataset.recipeId;
    const rating = button.dataset.rating;

    try {
        await api.post(`/api/recipe/${recipeId}/rate`, { rating: parseInt(rating) });
        showFlashMessage('Rating submitted successfully!', 'success');

        // Update UI to show the new rating
        const ratingContainer = button.closest('.recipe-rating');
        ratingContainer.querySelectorAll('button').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.rating <= rating);
        });
    } catch (error) {
        showFlashMessage('Failed to submit rating.', 'danger');
    }
}
