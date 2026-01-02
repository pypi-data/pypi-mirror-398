document.addEventListener('DOMContentLoaded', () => {
    const registerForm = document.querySelector('form');

    if (registerForm) {
        registerForm.addEventListener('submit', (event) => {
            const username = document.querySelector('#username').value.trim();
            const password = document.querySelector('#password').value.trim();

            if (username === '' || password === '') {
                alert('Please fill out all fields.');
                event.preventDefault(); // Prevent form submission
            } else if (password.length < 6) {
                alert('Password must be at least 6 characters long.');
                event.preventDefault(); // Prevent submission if password is too short
            }
        });
    }
});
