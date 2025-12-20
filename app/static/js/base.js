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
    removePhoto();
    closeCamera();
}

// Save new record
function saveNewRecord() {
    const description = document.getElementById('addDescription').value.trim();
    const amount = document.getElementById('addAmount').value;

    if (!description || !amount) {
        alert('Please fill in all required fields.');
        return;
    }

    const formData = new FormData();
    formData.append('description', description);
    formData.append('type', document.getElementById('addType').value);
    formData.append('amount', parseFloat(amount));
    formData.append('category', document.getElementById('addCategory').value);
    formData.append('account', document.getElementById('addAccount').value);
    formData.append('date', document.getElementById('addDate').value);
    formData.append('time', document.getElementById('addTime').value);

    if (selectedPhotoFile) {
        formData.append('photo', selectedPhotoFile);
    }

    fetch('/add_record', {
        method: 'POST',
        body: formData
    })
        .then(response => {
            if (response.ok) {
                closeAddModal();
                location.reload();
            } else {
                alert('Failed to add record.');
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


function loadNotifications() { // get notifications from the backend
    fetch('/notifications/get')
        .then(response => response.json()) // Parse JSON response
        .then(data => {
            notificationsData = data.notifications; // Save notifications 
            renderNotifications(); // Render list in UI
            updateNotificationBadge(data.notification_enabled); // Update unread count badge
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

        badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
        badge.style.display = 'flex';
    } else {

        badge.style.display = 'none';
    }
}

function updateNotificationBadge(notificationEnabled = true) {
    const unreadCount = notificationsData.filter(n => !n.is_read).length;
    const badge = document.getElementById('notificationBadge');

    // Only show badge if notifications are enabled in settings
    if (notificationEnabled && unreadCount > 0) {

        // Show badge and cap value at 99+
        badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
        badge.style.display = 'flex';
    } else {

        // Hide badge when no unread notifications or notifications disabled
        badge.style.display = 'none';
    }
}

function markAsRead(notificationId) {
    fetch(`/notifications/mark_read/${notificationId}`, {
        method: 'POST'
    }).then(() => {
        const notif = notificationsData.find(n => n.id === notificationId);
        if (notif) {
            notif.is_read = true; // Mark as read locally
            renderNotifications(); // Refresh UI
            // Reload to get the current notification_enabled state
            loadNotifications();
        }
    });
}

function markAllAsRead() {
    fetch('/notifications/mark_all_read', {
        method: 'POST'
    }).then(() => {
        notificationsData.forEach(n => n.is_read = true);
        renderNotifications();
        // Reload to get the current notification_enabled state
        loadNotifications();
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


// Store the selected photo file (from upload or camera capture)
let selectedPhotoFile = null;
// Store the active camera stream to manage camera lifecycle
let cameraStream = null;

// Trigger the hidden file input when upload button is clicked
function openFileUpload() {
    document.getElementById('photoInput').click();
}

// Handle file selection from the file input
function handlePhotoUpload(event) {
    const file = event.target.files[0];
    // Verify the file is an image before processing
    if (file && file.type.startsWith('image/')) {
        selectedPhotoFile = file;
        displayPhotoPreview(file);
    }
}

// Display the selected/captured photo in the preview area
function displayPhotoPreview(file) {
    const reader = new FileReader();
    reader.onload = function (e) {
        // Set the preview image source to the file data URL
        document.getElementById('previewImage').src = e.target.result;
        document.getElementById('photoPreview').style.display = 'block';
    };
    reader.readAsDataURL(file);
}

// Clear the selected photo and hide the preview
function removePhoto() {
    selectedPhotoFile = null;
    document.getElementById('photoPreview').style.display = 'none';
    // Reset the file input value to allow re-uploading the same file
    document.getElementById('photoInput').value = '';
}

// Request camera access and display the live video stream
async function openCamera() {
    try {
        // Request rear-facing camera with getUserMedia API
        cameraStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'environment' }
        });

        // Display the camera stream in the video element
        const video = document.getElementById('cameraStream');
        video.srcObject = cameraStream;
        video.style.display = 'block';
        document.getElementById('cameraControls').style.display = 'flex';

        // Hide upload options while camera is active
        document.querySelector('.upload-options').style.display = 'none';
    } catch (error) {
        alert('Camera access denied or unavailable');
    }
}

// Stop the camera stream and reset the UI
function closeCamera() {
    if (cameraStream) {
        // Stop all tracks to release camera resources
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }

    // Hide camera UI and restore upload options
    document.getElementById('cameraStream').style.display = 'none';
    document.getElementById('cameraControls').style.display = 'none';
    document.querySelector('.upload-options').style.display = 'flex';
}

// Capture the current video frame as a photo
function capturePhoto() {
    const video = document.getElementById('cameraStream');
    const canvas = document.getElementById('photoCanvas');
    const context = canvas.getContext('2d');

    // Set canvas dimensions to match video resolution
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    // Draw the current video frame onto the canvas
    context.drawImage(video, 0, 0);

    // Convert canvas to a Blob and create a File object
    canvas.toBlob(blob => {
        selectedPhotoFile = new File([blob], 'camera-photo.jpg', { type: 'image/jpeg' });
        displayPhotoPreview(selectedPhotoFile);
        closeCamera();
    }, 'image/jpeg');
}