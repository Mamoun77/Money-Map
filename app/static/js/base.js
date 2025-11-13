function toggleUserMenu() { // when pressing the username button
    const dropdown = document.getElementById('userDropdown');
    dropdown.classList.toggle('active');
}

// Close dropdown username menu when clicking outside
document.addEventListener('click', function (event) {
    const userMenu = document.querySelector('.user-menu');
    if (!userMenu.contains(event.target)) {
        document.getElementById('userDropdown').classList.remove('active');
    }
});

// the add record button
function addRecord() {
    // Redirect to add record page or open modal
}


document.getElementById('username').textContent = username;
// Display username
