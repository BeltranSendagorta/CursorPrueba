// Para el dashboard de usuario
document.addEventListener('DOMContentLoaded', function() {
    // Navegación
    const navLinks = document.querySelectorAll('.nav-links a');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            showSection(targetId);
            
            // Actualizar clase active
            navLinks.forEach(l => l.parentElement.classList.remove('active'));
            this.parentElement.classList.add('active');
        });
    });

    // Logout
    document.getElementById('logoutBtn').addEventListener('click', function() {
        window.location.href = '/logout';
    });

    // Añadir efecto hover a los días de guardia
    const diasGuardia = document.querySelectorAll('.calendario td.guardia');
    diasGuardia.forEach(dia => {
        dia.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.1)';
        });
        dia.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1.05)';
        });
    });
});

function showSection(sectionId) {
    document.querySelectorAll('.content section').forEach(section => {
        section.classList.add('hidden');
    });
    document.getElementById(sectionId).classList.remove('hidden');
}

function cambiarAño(año) {
    window.location.href = `/user/dashboard?año=${año}#guardias`;
}

function mostrarDetallesGuardia(fecha) {
    // Formatear la fecha para mostrarla de manera más amigable
    const fechaObj = new Date(fecha);
    const opciones = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    const fechaFormateada = fechaObj.toLocaleDateString('es-ES', opciones);
    
    alert(`Tienes guardia el ${fechaFormateada}`);
} 