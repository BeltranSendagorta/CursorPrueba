document.addEventListener('DOMContentLoaded', function() {
    // Datos de ejemplo (en una aplicación real, esto vendría de una base de datos)
    let volunteers = {
        1: {
            id: 1,
            name: 'Beltrán',
            roles: ['patron', 'socorrista'],
            courses: {
                'Primeros Auxilios': 'completed',
                'Comunicaciones': 'completed',
                'Navegación Básica': 'completed',
                'Navegación Avanzada': 'pending'
            }
        }
    };

    // Manejador para cambios en los cursos
    document.querySelectorAll('.course-status').forEach(select => {
        select.addEventListener('change', function() {
            const card = this.closest('.volunteer-card');
            card.classList.add('has-changes');
        });
    });

    // Manejador para guardar cambios
    document.querySelectorAll('.save-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const volunteerId = this.dataset.id;
            const card = this.closest('.volunteer-card');
            const courses = {};
            
            card.querySelectorAll('.course-item').forEach(item => {
                const courseName = item.querySelector('span').textContent;
                const status = item.querySelector('select').value;
                courses[courseName] = status;
            });

            // Aquí irían las llamadas a la API para guardar los cambios
            console.log('Guardando cambios para voluntario:', volunteerId, courses);
            
            // Simulamos una actualización exitosa
            card.classList.remove('has-changes');
            showNotification('Cambios guardados correctamente');
        });
    });

    // Función para abrir el modal de edición
    function openEditModal(volunteerId) {
        const volunteer = volunteers[volunteerId];
        const modal = document.getElementById('editModal');
        const form = document.getElementById('editVolunteerForm');
        
        // Rellenar el formulario con los datos actuales
        document.getElementById('editVolunteerId').value = volunteerId;
        document.getElementById('editName').value = volunteer.name;
        
        // Marcar los roles actuales
        document.querySelectorAll('input[name="roles"]').forEach(checkbox => {
            checkbox.checked = volunteer.roles.includes(checkbox.value);
        });
        
        modal.style.display = 'block';
    }

    // Función para cerrar el modal
    function closeEditModal() {
        document.getElementById('editModal').style.display = 'none';
    }

    // Manejador del formulario de edición
    document.getElementById('editVolunteerForm').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const volunteerId = document.getElementById('editVolunteerId').value;
        const name = document.getElementById('editName').value;
        const roles = Array.from(document.querySelectorAll('input[name="roles"]:checked'))
            .map(checkbox => checkbox.value);
        
        // Actualizar los datos
        volunteers[volunteerId] = {
            ...volunteers[volunteerId],
            name: name,
            roles: roles
        };
        
        // Actualizar la tarjeta del voluntario en la interfaz
        updateVolunteerCard(volunteerId);
        
        // Mostrar notificación y cerrar modal
        showNotification('Cambios guardados correctamente');
        closeEditModal();
    });

    // Función para actualizar la tarjeta del voluntario
    function updateVolunteerCard(volunteerId) {
        const volunteer = volunteers[volunteerId];
        const card = document.querySelector(`.volunteer-card[data-volunteer-id="${volunteerId}"]`);
        
        if (card) {
            card.querySelector('h3').textContent = volunteer.name;
            card.querySelector('.roles').textContent = formatRoles(volunteer.roles);
        }
    }

    // Función para formatear los roles
    function formatRoles(roles) {
        return roles.map(role => 
            role.charAt(0).toUpperCase() + role.slice(1)
        ).join(', ');
    }

    // Función para mostrar notificaciones
    function showNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'notification';
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    // Cerrar modal al hacer clic fuera
    window.onclick = function(event) {
        const modal = document.getElementById('editModal');
        if (event.target === modal) {
            closeEditModal();
        }
    }

    // Búsqueda de voluntarios
    const searchInput = document.getElementById('volunteerSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            document.querySelectorAll('.volunteer-card').forEach(card => {
                const name = card.querySelector('h3').textContent.toLowerCase();
                card.style.display = name.includes(searchTerm) ? 'block' : 'none';
            });
        });
    }

    let changesNeedSaving = false;

    // Función para manejar cambios
    function handleChanges() {
        changesNeedSaving = true;
        document.getElementById('saveIndicator').style.display = 'block';
    }

    // Función para guardar cambios
    async function saveVolunteerChanges(volunteerId) {
        const roles = Array.from(document.querySelectorAll('input[name="roles"]:checked'))
            .map(checkbox => checkbox.value);
        
        const courses = Array.from(document.querySelectorAll('.course-item'))
            .map(item => ({
                curso_id: item.dataset.cursoId,
                estado: item.querySelector('select').value
            }));

        try {
            const response = await fetch('/api/update_volunteer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    id: volunteerId,
                    roles: roles,
                    cursos: courses
                })
            });

            const data = await response.json();
            
            if (data.success) {
                changesNeedSaving = false;
                document.getElementById('saveIndicator').style.display = 'none';
                showNotification('Cambios guardados correctamente');
                updateVolunteerCard(volunteerId);
            } else {
                throw new Error(data.error || 'Error al guardar los cambios');
            }
        } catch (error) {
            showNotification('Error: ' + error.message, 'error');
        }
    }

    // Manejar cierre de sesión
    document.getElementById('logoutBtn').addEventListener('click', async function(e) {
        e.preventDefault();
        
        if (changesNeedSaving) {
            const confirm = window.confirm('Hay cambios sin guardar. ¿Desea guardarlos antes de salir?');
            if (confirm) {
                await saveAllChanges();
            }
        }
        
        // Cerrar sesión
        window.location.href = '/logout';
    });

    // Función para guardar todos los cambios pendientes
    async function saveAllChanges() {
        const volunteers = document.querySelectorAll('.volunteer-card');
        for (let volunteer of volunteers) {
            const volunteerId = volunteer.dataset.volunteerId;
            if (volunteer.classList.contains('has-changes')) {
                await saveVolunteerChanges(volunteerId);
            }
        }
    }

    // Detectar cambios en roles y cursos
    document.addEventListener('change', function(e) {
        if (e.target.matches('input[name="roles"]') || 
            e.target.matches('.course-status')) {
            handleChanges();
            e.target.closest('.volunteer-card').classList.add('has-changes');
        }
    });

    // Prevenir cierre accidental de la página
    window.addEventListener('beforeunload', function(e) {
        if (changesNeedSaving) {
            e.preventDefault();
            e.returnValue = '';
        }
    });
}); 