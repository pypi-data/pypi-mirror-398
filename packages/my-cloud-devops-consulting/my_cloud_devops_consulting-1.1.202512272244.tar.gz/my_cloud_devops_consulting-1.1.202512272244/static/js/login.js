document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');

    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            event.preventDefault(); // Prevent default form submission

            // Get form values
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value.trim();

            // Basic input validation
            if (!username || !password) {
                showAlert('Please fill out all fields.', 'danger');
                return;
            }

            // Successful validation message
            // showAlert(`Logging in with username: ${username}`, 'success');

            // TODO: Implement form submission logic (e.g., AJAX request)
            // Create an object with the form data
            let formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);

            // Send the form data to the server using fetch
            fetch('/login', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.status=="200") {
                    showAlert('Login successful!', 'success');
                    // Redirect to another page or perform other actions on success
                    window.location.href = '/';
                } else {
                    showAlert(data.message || 'Login failed. Please try again.', 'danger');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('An error occurred. Please try again later.', 'danger');
            });

        });
    }

    // Function to show alert messages
    function showAlert(message, type) {
        const existingAlert = document.querySelector('.alert');
        if (existingAlert) existingAlert.remove(); // Remove existing alerts

        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.role = 'alert';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        // Insert alert message above the form
        loginForm.parentNode.insertBefore(alert, loginForm);

        // Automatically remove alert after 3 seconds
        setTimeout(() => {
            if (alert) alert.remove();
        }, 3000);
    }
});
