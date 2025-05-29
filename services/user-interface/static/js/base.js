// Common API functions
const api = {
    async post(url, data) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error('Network response was not ok');
            return await response.json();
        } catch (error) {
            console.error('Error:', error);
            throw error;
        }
    },

    async get(url) {
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error('Network response was not ok');
            return await response.json();
        } catch (error) {
            console.error('Error:', error);
            throw error;
        }
    },

    async delete(url) {
        try {
            const response = await fetch(url, { method: 'DELETE' });
            if (!response.ok) throw new Error('Network response was not ok');
            return await response.json();
        } catch (error) {
            console.error('Error:', error);
            throw error;
        }
    }
};

// Flash message helper
function showFlashMessage(message, type = 'info') {
    const flashContainer = document.createElement('div');
    flashContainer.className = `alert alert-${type} alert-dismissible fade show`;
    flashContainer.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.querySelector('.container').insertAdjacentElement('afterbegin', flashContainer);
    setTimeout(() => flashContainer.remove(), 5000);
}

// Form submission helper
async function handleFormSubmit(form, url, successCallback) {
    try {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        const result = await api.post(url, data);
        if (successCallback) successCallback(result);
    } catch (error) {
        showFlashMessage('An error occurred. Please try again.', 'danger');
    }
}
