document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const loginModal = document.getElementById('loginModal');
    const userMenu = document.getElementById('userMenu');
    const logoutBtn = document.getElementById('logoutBtn');

    // Simular base de datos de usuarios
    const users = {
        'admin': {
            password: 'admin123',
            role: 'Administrador',
            name: 'Administrador Principal',
            specialties: ['Patrón', 'Socorrista'],
            guardGroup: 'Grupo 1',
            hours: 150,
            emergencies: 25
        },
        // Añadir más usuarios aquí
    };

    loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        if (users[username] && users[username].password === password) {
            loginModal.style.display = 'none';
            userMenu.style.display = 'block';
            document.getElementById('userName').textContent = users[username].name;
            loadUserProfile(users[username]);
        } else {
            alert('Usuario o contraseña incorrectos');
        }
    });

    logoutBtn.addEventListener('click', () => {
        loginModal.style.display = 'block';
        userMenu.style.display = 'none';
        document.getElementById('userName').textContent = '';
    });

    function loadUserProfile(user) {
        document.getElementById('profileName').textContent = user.name;
        document.getElementById('profileRole').textContent = user.role;
        document.getElementById('profileSpec').textContent = user.specialties.join(', ');
        document.getElementById('guardGroup').textContent = user.guardGroup;
        document.getElementById('totalHours').textContent = user.hours;
        document.getElementById('totalEmergencies').textContent = user.emergencies;
    }

    function handleCredentialResponse(response) {
        // Decodificar el token JWT
        const responsePayload = decodeJwtResponse(response.credential);
        
        // Extraer información del usuario
        const userData = {
            email: responsePayload.email,
            name: responsePayload.name,
            picture: responsePayload.picture
        };

        // Cerrar el modal de login
        document.getElementById('loginModal').style.display = 'none';
        
        // Mostrar el menú de usuario
        const userMenu = document.getElementById('userMenu');
        userMenu.style.display = 'block';
        
        // Actualizar el nombre del usuario
        document.getElementById('userName').textContent = userData.name;
        
        // Cargar el perfil del usuario
        loadUserProfile({
            name: userData.name,
            role: 'Voluntario',
            specialties: ['Por asignar'],
            guardGroup: 'Por asignar',
            hours: 0,
            emergencies: 0
        });
    }

    function decodeJwtResponse(token) {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
        return JSON.parse(jsonPayload);
    }

    // Base de datos simulada usando localStorage
    const initializeDatabase = () => {
        if (!localStorage.getItem('volunteers')) {
            // Voluntario de prueba
            const initialVolunteers = [{
                id: 1,
                name: "Juan Pérez",
                role: "Patrón de Emergencias",
                specialties: ["Patrón", "Socorrista"],
                guardGroup: "Grupo 1",
                hours: 150,
                emergencies: 25,
                email: "juan.perez@example.com",
                avatar: "https://via.placeholder.com/60"
            }];
            localStorage.setItem('volunteers', JSON.stringify(initialVolunteers));
        }

        if (!localStorage.getItem('emergencies')) {
            const initialEmergencies = [{
                id: 1,
                type: "maritimo",
                date: "2024-03-15",
                description: "Rescate embarcación a la deriva",
                volunteers: ["Juan Pérez"],
                status: "Completada"
            }];
            localStorage.setItem('emergencies', JSON.stringify(initialEmergencies));
        }
    };

    // Cargar voluntarios
    const loadVolunteers = () => {
        const volunteers = JSON.parse(localStorage.getItem('volunteers')) || [];
        const grid = document.getElementById('volunteersGrid');
        grid.innerHTML = '';

        volunteers.forEach(volunteer => {
            const card = document.createElement('div');
            card.className = 'volunteer-card';
            card.innerHTML = `
                <div class="volunteer-header">
                    <img src="${volunteer.avatar}" alt="${volunteer.name}" class="volunteer-avatar">
                    <div>
                        <h3>${volunteer.name}</h3>
                        <p>${volunteer.role}</p>
                    </div>
                </div>
                <div class="volunteer-info">
                    <p><strong>Especialidades:</strong> ${volunteer.specialties.join(', ')}</p>
                    <p><strong>Grupo de Guardia:</strong> ${volunteer.guardGroup}</p>
                    <p><strong>Horas:</strong> ${volunteer.hours}</p>
                    <p><strong>Emergencias:</strong> ${volunteer.emergencies}</p>
                </div>
            `;
            grid.appendChild(card);
        });
    };

    // Cargar emergencias
    const loadEmergencies = () => {
        const emergencies = JSON.parse(localStorage.getItem('emergencies')) || [];
        const list = document.getElementById('emergenciesList');
        list.innerHTML = '';

        emergencies.forEach(emergency => {
            const card = document.createElement('div');
            card.className = 'emergency-card';
            card.innerHTML = `
                <h3>${emergency.type.toUpperCase()}</h3>
                <p><strong>Fecha:</strong> ${emergency.date}</p>
                <p><strong>Descripción:</strong> ${emergency.description}</p>
                <p><strong>Voluntarios:</strong> ${emergency.volunteers.join(', ')}</p>
                <p><strong>Estado:</strong> ${emergency.status}</p>
            `;
            list.appendChild(card);
        });
    };

    // Inicializar la aplicación
    initializeDatabase();
    loadVolunteers();
    loadEmergencies();

    // Manejar el formulario de contacto
    const contactForm = document.getElementById('contactForm');
    contactForm.addEventListener('submit', (e) => {
        e.preventDefault();
        alert('Mensaje enviado correctamente');
        contactForm.reset();
    });

    // Filtros de emergencias
    const typeFilter = document.getElementById('emergencyTypeFilter');
    typeFilter.addEventListener('change', () => {
        loadEmergencies();
    });

    // Función para comprobar si el usuario es administrador
    const isAdmin = (user) => {
        return user.role === 'Administrador';
    };

    // Mostrar/ocultar controles de administrador
    const updateAdminControls = (user) => {
        const adminControls = document.getElementById('adminControls');
        if (isAdmin(user)) {
            adminControls.style.display = 'block';
        } else {
            adminControls.style.display = 'none';
        }
    };
}); 