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

// Dark mode functionality
function applyTheme(isDark) {
    if (isDark) {
        document.body.classList.add('dark-mode');
        document.getElementById('themeIcon').textContent = '☀️';
    } else {
        document.body.classList.remove('dark-mode');
        document.getElementById('themeIcon').textContent = '🌙';
    }
}

// Fetch user theme preference on page load
fetch('/get_theme')
    .then(response => response.json())
    .then(data => {
        applyTheme(data.dark_mode);
    });

// Toggle theme
function toggleTheme() {
    const isDark = document.body.classList.toggle('dark-mode');
    document.getElementById('themeIcon').textContent = isDark ? '☀️' : '🌙';

    fetch('/update_theme', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ dark_mode: isDark })
    });
}


// The Notification functionality code

// for storing notifications fetched from the backend
let notificationsData = [];

function toggleNotifications() {
    // Get the dropdown element
    const dropdown = document.getElementById('notificationDropdown');

    // Toggle open/close state
    dropdown.classList.toggle('active');

    // Only fetch notifications when dropdown is opened
    if (dropdown.classList.contains('active')) {
        loadNotifications();
    }
}

function loadNotifications() {
    // Fetch notifications from backend
    fetch('/notifications/get')
        .then(response => response.json()) // Parse JSON response
        .then(data => {
            notificationsData = data;       // Save notifications locally
            renderNotifications();          // Render list in UI
            updateNotificationBadge();      // Update unread count badge
        });
}

function renderNotifications() {
    const listElement = document.getElementById('notificationList');

    // If there are no notifications, show empty state
    if (notificationsData.length === 0) {
        listElement.innerHTML = '<div class="notification-empty">No notifications</div>';
        return;
    }

    // Build HTML for each notification
    listElement.innerHTML = notificationsData.map(notif => `
        <div class="notification-item ${notif.is_read ? '' : 'unread'}" 
             onclick="markAsRead(${notif.id})">
            <div class="notification-item-title">${notif.title}</div>
            <div class="notification-item-message">${notif.message || ''}</div>
            <div class="notification-item-time">${notif.created_at}</div>
        </div>
    `).join(''); // Join array into one HTML string
}

function updateNotificationBadge() {
    // Count notifications that are not read
    const unreadCount = notificationsData.filter(n => !n.is_read).length;
    const badge = document.getElementById('notificationBadge');

    if (unreadCount > 0) {
        // Show badge and cap value at 99+
        badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
        badge.style.display = 'flex';
    } else {
        // Hide badge when no unread notifications
        badge.style.display = 'none';
    }
}

function markAsRead(notificationId) {
    // Send request to mark single notification as read
    fetch(`/notifications/mark_read/${notificationId}`, {
        method: 'POST'
    }).then(() => {
        // Update local notification state
        const notif = notificationsData.find(n => n.id === notificationId);
        if (notif) {
            notif.is_read = true;   // Mark as read locally
            renderNotifications(); // Refresh UI
            updateNotificationBadge();
        }
    });
}

function markAllAsRead() {
    // Send request to mark all notifications as read
    fetch('/notifications/mark_all_read', {
        method: 'POST'
    }).then(() => {
        // Update all notifications locally
        notificationsData.forEach(n => n.is_read = true);
        renderNotifications();
        updateNotificationBadge();
    });
}

// Close notification dropdown when clicking outside of it
document.addEventListener('click', function (event) {
    const notificationBtn = document.getElementById('notificationBtn');
    const notificationDropdown = document.getElementById('notificationDropdown');

    // If click is outside both the button and dropdown → close dropdown
    if (!notificationBtn.contains(event.target) && !notificationDropdown.contains(event.target)) {
        notificationDropdown.classList.remove('active');
    }
});

// Load notifications on page load (for badge count)
loadNotifications();
