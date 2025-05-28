document.addEventListener('DOMContentLoaded', function () {
    // Create group form handling
    const createGroupForm = document.getElementById('createGroupForm');
    if (createGroupForm) {
        createGroupForm.addEventListener('submit', handleCreateGroup);
    }

    // Join group form handling
    const joinGroupForm = document.getElementById('joinGroupForm');
    if (joinGroupForm) {
        joinGroupForm.addEventListener('submit', handleJoinGroup);
    }

    // Member search functionality
    const memberSearchInput = document.querySelector('.member-search input');
    if (memberSearchInput) {
        memberSearchInput.addEventListener('input', handleMemberSearch);
    }

    // Group preference changes
    const preferenceInputs = document.querySelectorAll('.group-preferences input');
    preferenceInputs.forEach(input => {
        input.addEventListener('change', handlePreferenceChange);
    });

    // Initialize roulette functionality
    initializeRoulette();
});

async function handleCreateGroup(event) {
    event.preventDefault();
    const form = event.currentTarget;

    try {
        const result = await api.post('/api/group/create', {
            name: form.groupName.value,
            description: form.groupDescription.value
        });

        window.location.href = `/eat-together/group/${result.id}/settings`;
    } catch (error) {
        showFlashMessage('Failed to create group.', 'danger');
    }
}

async function handleJoinGroup(event) {
    event.preventDefault();
    const form = event.currentTarget;

    try {
        const groupCode = form.groupCode.value;
        const group = await api.get(`/eat-together/group/${groupCode}`);
        window.location.href = `/eat-together/group/${group.id}/settings`;
    } catch (error) {
        showFlashMessage('Invalid group code or group not found.', 'danger');
    }
}

let searchTimeout;
async function handleMemberSearch(event) {
    clearTimeout(searchTimeout);
    const query = event.target.value.trim();
    const resultsContainer = document.querySelector('.member-search-results');

    if (query) {
        searchTimeout = setTimeout(async () => {
            try {
                const results = await api.get(`/api/user/search?email=${encodeURIComponent(query)}`);
                displayMemberSearchResults(results, resultsContainer);
            } catch (error) {
                showFlashMessage('Failed to search for users.', 'danger');
            }
        }, 500);
    } else {
        resultsContainer.innerHTML = '';
    }
}

function displayMemberSearchResults(users, container) {
    if (!users.length) {
        container.innerHTML = '<p class="text-muted">No users found</p>';
        return;
    }

    container.innerHTML = users.map(user => `
        <div class="member-result d-flex justify-content-between align-items-center p-2">
            <span>${user.email}</span>
            <button class="btn btn-sm btn-primary" onclick="addMember('${user.id}')">
                Add Member
            </button>
        </div>
    `).join('');
}

async function addMember(userId) {
    const groupId = document.querySelector('[data-group-id]').dataset.groupId;

    try {
        await api.post(`/api/group/${groupId}/member`, { member_id: userId });
        showFlashMessage('Member added successfully!', 'success');
        location.reload();
    } catch (error) {
        showFlashMessage('Failed to add member.', 'danger');
    }
}

async function removeMember(groupId, memberId) {
    if (!confirm('Are you sure you want to remove this member?')) return;

    try {
        await api.delete(`/api/group/${groupId}/member/${memberId}`);
        showFlashMessage('Member removed successfully!', 'success');
        location.reload();
    } catch (error) {
        showFlashMessage('Failed to remove member.', 'danger');
    }
}

async function handlePreferenceChange(event) {
    const input = event.target;
    const groupId = document.querySelector('[data-group-id]').dataset.groupId;
    const preferences = {
        [input.name]: input.type === 'checkbox' ? input.checked : input.value
    };

    try {
        await api.post(`/eat-together/${groupId}/update-guest`, preferences);
    } catch (error) {
        showFlashMessage('Failed to update preferences.', 'danger');
        // Revert the change
        input.checked = !input.checked;
    }
}

function initializeRoulette() {
    const rouletteModal = document.getElementById('rouletteModal');
    if (!rouletteModal) return;

    rouletteModal.addEventListener('show.bs.modal', async function () {
        const resultText = document.getElementById('roulette-result');
        const spinner = document.querySelector('.roulette-spinner');

        try {
            resultText.textContent = 'Finding a random restaurant...';
            spinner.style.display = 'block';

            // Simulate spinning animation while fetching result
            const groupId = document.querySelector('[data-group-id]').dataset.groupId;
            const matches = await api.get(`/eat-together/${groupId}/food-matches`);

            // Randomly select one restaurant
            const randomMatch = matches[Math.floor(Math.random() * matches.length)];

            // Show result after animation
            setTimeout(() => {
                spinner.style.display = 'none';
                resultText.textContent = randomMatch.name;

                const resultDetails = document.createElement('div');
                resultDetails.innerHTML = `
                    <p class="text-muted">${randomMatch.cuisine_type} • ${randomMatch.price_range}</p>
                    <p>${randomMatch.description}</p>
                    <a href="/food/restaurant/${randomMatch.id}" class="btn btn-primary mt-3">View Details</a>
                `;
                resultText.appendChild(resultDetails);
            }, 2000);
        } catch (error) {
            showFlashMessage('Failed to get restaurant recommendations.', 'danger');
            const modal = bootstrap.Modal.getInstance(rouletteModal);
            modal.hide();
        }
    });
}
