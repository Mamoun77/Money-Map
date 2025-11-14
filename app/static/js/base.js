// Toggle user dropdown menu
function toggleUserMenu() {
    const dropdown = document.getElementById('userDropdown');
    dropdown.classList.toggle('active');
}

// Close dropdown when clicking outside
document.addEventListener('click', function (event) {
    const userMenu = document.querySelector('.user-menu');
    if (!userMenu.contains(event.target)) {
        document.getElementById('userDropdown').classList.remove('active');
    }
});

// Set username
document.getElementById('username').textContent = username;

// Open add record modal
function addRecord() {
    // Set current date and time as defaults
    const now = new Date();
    const dateStr = now.toISOString().split('T')[0]; // for getting YYYY-MM-DD format
    const timeStr = now.toTimeString().slice(0, 5); // for getting HH:MM format

    document.getElementById('addDate').value = dateStr;
    document.getElementById('addTime').value = timeStr;

    // Clear form fields
    document.getElementById('addDescription').value = '';
    document.getElementById('addAmount').value = '';

    // Show modal
    document.getElementById('addModal').classList.add('active');
}

// Close add record modal
function closeAddModal() {
    document.getElementById('addModal').classList.remove('active');
}

// Save new record
function saveNewRecord() {
    // Get form values
    const description = document.getElementById('addDescription').value.trim();
    const amount = document.getElementById('addAmount').value;

    // Validate required fields
    if (!description || !amount) {
        alert('Please fill in all required fields.');
        return;
    }

    const formData = {
        description: description,
        type: document.getElementById('addType').value,
        amount: parseFloat(amount),
        category: document.getElementById('addCategory').value,
        account: document.getElementById('addAccount').value,
        date: document.getElementById('addDate').value,
        time: document.getElementById('addTime').value
    };

    fetch('/add_record', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
        .then(response => {
            if (response.ok) {
                closeAddModal();
                location.reload();
            } else {
                alert('Failed to update the record.');
            }
        });
}

// Close modal when clicking outside
document.getElementById('addModal').addEventListener('click', function (e) {
    if (e.target === this) {
        closeAddModal();
    }
});