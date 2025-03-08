document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');

    // Definir usuarios válidos
    const users = {
        'admin': {
            password: 'admin123',
            role: 'admin',
            name: 'Administrador'
        },
        'beltran': {
            password: 'arriluce',
            role: 'user',
            name: 'Beltrán',
            specialties: ['Patrón', 'Socorrista'],
            guardGroup: 'Grupo 1'
        }
    };

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value.toLowerCase();
        const password = document.getElementById('password').value;

        try {
            const user = users[username];
            
            if (user && user.password === password) {
                // Guardar información del usuario en sessionStorage
                sessionStorage.setItem('currentUser', JSON.stringify({
                    username: username,
                    name: user.name,
                    role: user.role,
                    specialties: user.specialties,
                    guardGroup: user.guardGroup
                }));

                // Redirigir según el rol (rutas relativas)
                if (user.role === 'admin') {
                    window.location.href = 'admin/dashboard.html';
                } else {
                    window.location.href = 'user/dashboard.html';
                }
            } else {
                alert('Usuario o contraseña incorrectos');
            }
        } catch (error) {
            console.error('Error de autenticación:', error);
            alert('Error al iniciar sesión');
        }
    });
});

function handleCredentialResponse(response) {
    // Manejar la respuesta de Google Sign-In
    // Redirigir según el rol del usuario
} 