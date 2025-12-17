const emailStep = document.getElementById('emailStep');
const codeStep = document.getElementById('codeStep');
const passwordStep = document.getElementById('passwordStep');

const emailForm = document.getElementById('emailForm');
const codeForm = document.getElementById('codeForm');
const passwordForm = document.getElementById('passwordForm');

const emailInput = document.getElementById('email');
const codeInput = document.getElementById('code');
const newPasswordInput = document.getElementById('newPassword');
const confirmPasswordInput = document.getElementById('confirmPassword');

const userEmailSpan = document.getElementById('userEmail');
const resendBtn = document.getElementById('resendBtn');

let userEmail = '';

// Step 1: Send verification code
emailForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearError('emailError');

    const email = emailInput.value.trim();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!emailRegex.test(email)) {
        showError('emailError', 'Please enter a valid email address');
        return;
    }

    try {
        const response = await fetch('/recover/send_code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });

        const data = await response.json();

        if (response.ok) {
            userEmail = email;
            userEmailSpan.textContent = email;
            showStep(codeStep);
        } else {
            showError('emailError', data.message || 'Email not found');
        }
    } catch (error) {
        showError('emailError', 'An error occurred. Please try again.');
    }
});

// Step 2: Verify code that the user provided
codeForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearError('codeError');

    const code = codeInput.value.trim();

    if (code.length !== 6) {    // if the code is not 6 digits
        showError('codeError', 'Please enter a 6-digit code');
        return;
    }

    try {
        const response = await fetch('/recover/verify_code', {  // sends a post request to verify the code
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: userEmail, code })
        });

        const data = await response.json();

        if (response.ok) {
            showStep(passwordStep);
        } else {
            showError('codeError', data.message || 'Invalid code');
        }
    } catch (error) {
        showError('codeError', 'An error occurred. Please try again.');
    }
});

// Step 3: Reset password if the code is verified
passwordForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearError('newPasswordError');
    clearError('confirmPasswordError');

    const newPassword = newPasswordInput.value;
    const confirmPassword = confirmPasswordInput.value;

    if (newPassword.length < 6) {
        showError('newPasswordError', 'Password must be at least 6 characters');
        return;
    }

    if (newPassword !== confirmPassword) {
        showError('confirmPasswordError', 'Passwords do not match');
        return;
    }

    try {
        const response = await fetch('/recover/reset_password', { // sends a post request with the new password
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: userEmail, password: newPassword })
        });

        const data = await response.json();

        if (response.ok) {
            alert('Password reset successful! Redirecting to login...');
            window.location.href = '/login';
        } else {
            showError('newPasswordError', data.message || 'Failed to reset password');
        }
    } catch (error) {
        showError('newPasswordError', 'An error occurred. Please try again.');
    }
});

// Resend code
resendBtn.addEventListener('click', async () => {
    resendBtn.disabled = true;
    resendBtn.textContent = 'Sending...';

    try {
        const response = await fetch('/recover/send_code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: userEmail })
        });

        if (response.ok) {
            alert('New code sent to your email!');
        } else {
            alert('Failed to resend code');
        }
    } catch (error) {
        alert('An error occurred');
    } finally {
        resendBtn.disabled = false;
        resendBtn.textContent = 'Resend Code';
    }
});

// Helper functions
function showStep(step) {
    document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
    step.classList.add('active');
}

function showError(elementId, message) { // Shows an error message in the given element
    const errorElement = document.getElementById(elementId);
    errorElement.textContent = message;
    errorElement.style.display = 'block';
}

function clearError(elementId) { // Clears the error message in the given element
    const errorElement = document.getElementById(elementId);
    errorElement.style.display = 'none';
}