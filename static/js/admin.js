// Para el dashboard de administrador
document.addEventListener('DOMContentLoaded', function() {
    // Manejar el cierre de sesión
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            
            // Verificar si hay cambios sin guardar
            if (window.changesNeedSaving) {
                const confirm = window.confirm('Hay cambios sin guardar. ¿Desea guardarlos antes de salir?');
                if (confirm) {
                    try {
                        await saveAllChanges();
                    } catch (error) {
                        console.error('Error al guardar cambios:', error);
                    }
                }
            }
            
            // Redirigir al logout
            window.location.href = '/logout';
        });
    }

    // Navegación
    const navLinks = document.querySelectorAll('.nav-links a');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            showSection(targetId);
        });
    });

    // Formulario nuevo voluntario
    const formNuevoVoluntario = document.getElementById('form-nuevo-voluntario');
    if (formNuevoVoluntario) {
        formNuevoVoluntario.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Verificar que al menos un rol está seleccionado
            const rolesSeleccionados = Array.from(document.querySelectorAll('input[name="roles"]:checked'))
                .map(cb => cb.value);
            
            if (rolesSeleccionados.length === 0) {
                alert('Debe seleccionar al menos un rol para el voluntario');
                return;
            }

            const formData = {
                nombre: document.getElementById('nombre').value,
                apellidos: document.getElementById('apellidos').value,
                dni: document.getElementById('dni').value,
                telefono: document.getElementById('telefono').value,
                email: document.getElementById('email').value,
                password: document.getElementById('password').value,
                roles: rolesSeleccionados
            };

            fetch('/admin/voluntario/nuevo', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Voluntario creado exitosamente');
                    formNuevoVoluntario.reset();
                    location.reload(); // Recargar para ver el nuevo voluntario
                } else {
                    alert(data.message || 'Error al crear voluntario');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error al crear voluntario');
            });
        });
    }

    // Formulario nuevo curso
    const formNuevoCurso = document.getElementById('form-nuevo-curso');
    if (formNuevoCurso) {
        formNuevoCurso.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = {
                nombre: document.getElementById('curso-nombre').value,
                descripcion: document.getElementById('curso-descripcion').value,
                horas: document.getElementById('curso-horas').value
            };

            fetch('/admin/curso/nuevo', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Curso creado exitosamente');
                    formNuevoCurso.reset();
                    showSection('cursos');
                    // Recargar lista de cursos
                    location.reload();
                } else {
                    alert(data.message || 'Error al crear curso');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error al crear curso');
            });
        });
    }

    // Modal de cursos
    const modal = document.getElementById('modal-cursos');
    const span = document.getElementsByClassName('close')[0];
    
    // Botones para ver cursos
    document.querySelectorAll('.btn-ver-cursos').forEach(button => {
        button.addEventListener('click', function() {
            const voluntarioId = this.getAttribute('data-id');
            fetch(`/admin/voluntario/${voluntarioId}/cursos`)
                .then(response => response.json())
                .then(data => {
                    mostrarCursosVoluntario(data);
                    modal.style.display = 'block';
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error al cargar los cursos');
                });
        });
    });

    // Cerrar modal
    span.onclick = function() {
        modal.style.display = 'none';
    }

    window.onclick = function(event) {
        const modales = document.getElementsByClassName('modal');
        for (let modal of modales) {
            if (event.target == modal) {
                modal.style.display = "none";
            }
        }
    }

    // Modal de edición
    const modalEditar = document.getElementById('modal-editar-voluntario');
    const spanEditar = modalEditar.querySelector('.close');

    // Cerrar modal de edición
    spanEditar.onclick = function() {
        modalEditar.style.display = "none";
    }

    // Manejar clic en botón editar
    document.querySelectorAll('.btn-editar').forEach(button => {
        button.addEventListener('click', function() {
            const voluntarioId = this.getAttribute('data-id');
            cargarDatosVoluntario(voluntarioId);
        });
    });

    // Agregar manejador para edición de cursos
    document.querySelectorAll('.btn-editar-curso').forEach(button => {
        button.addEventListener('click', function() {
            const cursoId = this.getAttribute('data-id');
            cargarDatosCurso(cursoId);
        });
    });
});

function showSection(sectionId) {
    document.querySelectorAll('.content section').forEach(section => {
        section.classList.add('hidden');
    });
    document.getElementById(sectionId).classList.remove('hidden');
    
    document.querySelectorAll('.nav-links li').forEach(li => {
        li.classList.remove('active');
    });
    document.querySelector(`.nav-links a[href="#${sectionId}"]`).parentElement.classList.add('active');
}

function mostrarCursosVoluntario(data) {
    const container = document.getElementById('cursos-voluntario');
    let html = '<table class="cursos-table">';
    html += '<thead><tr><th>Curso</th><th>Estado</th><th>Acción</th></tr></thead><tbody>';
    
    data.cursos.forEach(curso => {
        html += `
            <tr>
                <td>${curso.nombre}</td>
                <td>${curso.estado || 'No iniciado'}</td>
                <td>
                    <select class="estado-curso" data-voluntario="${data.voluntario_id}" data-curso="${curso.id}">
                        <option value="pendiente" ${curso.estado === 'pendiente' ? 'selected' : ''}>Pendiente</option>
                        <option value="en_progreso" ${curso.estado === 'en_progreso' ? 'selected' : ''}>En Progreso</option>
                        <option value="completado" ${curso.estado === 'completado' ? 'selected' : ''}>Completado</option>
                    </select>
                </td>
            </tr>
        `;
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;

    // Agregar event listeners a los selects
    document.querySelectorAll('.estado-curso').forEach(select => {
        select.addEventListener('change', function() {
            const voluntarioId = this.getAttribute('data-voluntario');
            const cursoId = this.getAttribute('data-curso');
            const estado = this.value;

            fetch('/admin/voluntario/curso/actualizar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    voluntario_id: voluntarioId,
                    curso_id: cursoId,
                    estado: estado
                })
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    alert('Error al actualizar el estado del curso');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error al actualizar el estado del curso');
            });
        });
    });
}

// Cargar datos del voluntario
function cargarDatosVoluntario(voluntarioId) {
    fetch(`/admin/voluntario/${voluntarioId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.voluntario) {
                const voluntario = data.voluntario;
                console.log('Datos del voluntario:', voluntario); // Para depuración

                // Llenar el formulario con los datos
                document.getElementById('edit-voluntario-id').value = voluntario.id;
                document.getElementById('edit-nombre').value = voluntario.nombre || '';
                document.getElementById('edit-apellidos').value = voluntario.apellidos || '';
                document.getElementById('edit-dni').value = voluntario.dni || '';
                document.getElementById('edit-telefono').value = voluntario.telefono || '';
                document.getElementById('edit-email').value = voluntario.email || '';
                document.getElementById('edit-password').value = ''; // Siempre vacío para nueva contraseña

                // Limpiar todos los checkboxes primero
                document.querySelectorAll('input[name="edit-roles"]').forEach(checkbox => {
                    checkbox.checked = false;
                });

                // Marcar los roles que tiene el voluntario
                if (voluntario.roles && Array.isArray(voluntario.roles)) {
                    voluntario.roles.forEach(rol => {
                        const checkbox = document.querySelector(`input[name="edit-roles"][value="${rol}"]`);
                        if (checkbox) {
                            checkbox.checked = true;
                        }
                    });
                }

                // Mostrar el modal
                document.getElementById('modal-editar-voluntario').style.display = "block";
            } else {
                alert('Error al cargar los datos del voluntario');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al cargar los datos del voluntario');
        });
}

// Manejar envío del formulario de edición
document.getElementById('form-editar-voluntario').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const voluntarioId = document.getElementById('edit-voluntario-id').value;
    const formData = {
        nombre: document.getElementById('edit-nombre').value,
        apellidos: document.getElementById('edit-apellidos').value,
        telefono: document.getElementById('edit-telefono').value,
        email: document.getElementById('edit-email').value,
        password: document.getElementById('edit-password').value,
        roles: Array.from(document.querySelectorAll('input[name="edit-roles"]:checked'))
            .map(cb => cb.value)
    };

    fetch(`/admin/voluntario/${voluntarioId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Voluntario actualizado exitosamente');
            document.getElementById('modal-editar-voluntario').style.display = "none";
            location.reload();
        } else {
            alert(data.message || 'Error al actualizar voluntario');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al actualizar voluntario');
    });
});

function cargarDatosCurso(cursoId) {
    fetch(`/admin/curso/${cursoId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const curso = data.curso;
                document.getElementById('edit-curso-id').value = curso.id;
                document.getElementById('edit-curso-nombre').value = curso.nombre;
                document.getElementById('edit-curso-descripcion').value = curso.descripcion;
                document.getElementById('edit-curso-horas').value = curso.horas;
                modalEditarCurso.style.display = "block";
            } else {
                alert('Error al cargar los datos del curso');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al cargar los datos del curso');
        });
}

// Manejador para el formulario de edición de curso
document.getElementById('form-editar-curso').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const cursoId = document.getElementById('edit-curso-id').value;
    const formData = {
        nombre: document.getElementById('edit-curso-nombre').value,
        descripcion: document.getElementById('edit-curso-descripcion').value,
        horas: parseInt(document.getElementById('edit-curso-horas').value)
    };

    fetch(`/admin/curso/${cursoId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Curso actualizado exitosamente');
            modalEditarCurso.style.display = "none";
            location.reload();
        } else {
            alert(data.message || 'Error al actualizar curso');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al actualizar curso');
    });
}); 