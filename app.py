from flask import (
    Flask, 
    render_template, 
    request, 
    jsonify, 
    redirect, 
    url_for, 
    session,
    make_response
)
from database import CruzRojaDB
import os
from functools import wraps
from datetime import timedelta, datetime
import calendar

app = Flask(__name__, 
    static_url_path='',
    static_folder='static',
    template_folder='templates'
)
app.secret_key = os.urandom(24)
app.permanent_session_lifetime = timedelta(hours=5)

# Configuración para archivos estáticos
app.static_folder = 'static'

# Inicializar la base de datos como variable global
db = None

def get_db():
    global db
    if db is None:
        db = CruzRojaDB()
    return db

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('rol') != 'admin':
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def check_session():
    if request.endpoint and 'static' not in request.endpoint:
        if 'user_id' not in session and request.endpoint not in ['index', 'login', 'logout']:
            return redirect(url_for('index'))

@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('rol') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('user_dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({
            'success': False, 
            'message': 'DNI y contraseña son requeridos'
        }), 400
    
    database = get_db()
    user = database.verificar_usuario(data['username'], data['password'])
    
    if user:
        session['user_id'] = user['id']
        session['rol'] = user['rol']
        session['nombre'] = f"{user['nombre']} {user['apellidos']}"
        
        if user['rol'] == 'admin':
            return jsonify({'success': True, 'redirect': '/admin/dashboard'})
        else:
            return jsonify({'success': True, 'redirect': '/user/dashboard'})
    
    return jsonify({
        'success': False, 
        'message': 'DNI o contraseña incorrectos'
    }), 401

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    database = get_db()
    voluntarios = database.obtener_voluntarios()
    roles = database.obtener_roles()
    cursos = database.obtener_cursos()
    return render_template('admin/dashboard.html', 
                         voluntarios=voluntarios,
                         roles=roles,
                         cursos=cursos)

def generar_calendario(año, mes):
    """Genera el calendario para un mes específico"""
    return calendar.monthcalendar(año, mes)

def es_dia_guardia(fecha, guardias):
    """Verifica si una fecha específica es día de guardia"""
    return any(g['fecha'] == fecha for g in guardias)

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    database = get_db()
    user_id = session['user_id']
    user_data = database.obtener_datos_voluntario(user_id)
    
    if not user_data:
        session.clear()
        return redirect(url_for('index'))
    
    # Generar guardias para el voluntario
    database.generar_guardias_voluntario(user_id)
    
    # Obtener las guardias del año
    dias_guardia = database.obtener_guardias_por_año(user_id, 2025)
    proxima_guardia = database.obtener_proxima_guardia(user_id)
    
    # Generar calendarios para todos los meses
    calendarios = {}
    for mes in range(1, 13):
        calendarios[mes] = calendar.monthcalendar(2025, mes)
    
    return render_template('user/dashboard.html', 
                         user_data=user_data,
                         proxima_guardia=proxima_guardia,
                         calendarios=calendarios,
                         dias_guardia=dias_guardia,
                         año_actual=2025,
                         nombres_meses=[
                             'Enero', 'Febrero', 'Marzo', 'Abril',
                             'Mayo', 'Junio', 'Julio', 'Agosto',
                             'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
                         ])

@app.route('/api/update_volunteer', methods=['POST'])
def update_volunteer():
    if 'user_id' not in session or session['rol'] != 'admin':
        return jsonify({'success': False, 'error': 'No autorizado'})
    
    data = request.json
    try:
        # Actualizar roles
        get_db().actualizar_roles_voluntario(data['id'], data['roles'])
        
        # Actualizar cursos
        for curso in data['cursos']:
            get_db().actualizar_estado_curso(
                data['id'], 
                curso['curso_id'], 
                curso['estado']
            )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/logout')
def logout():
    # Limpiar toda la sesión
    session.clear()
    # Forzar la redirección al inicio
    return redirect(url_for('index')), 302

@app.route('/admin/voluntario/nuevo', methods=['POST'])
@admin_required
def nuevo_voluntario():
    data = request.get_json()
    
    # Validar datos requeridos
    required_fields = ['nombre', 'apellidos', 'dni', 'password', 'roles']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({
                'success': False, 
                'message': f'El campo {field} es requerido'
            })
    
    # Validar que haya al menos un rol seleccionado
    if not data['roles']:
        return jsonify({
            'success': False, 
            'message': 'Debe seleccionar al menos un rol'
        })
    
    database = get_db()
    if database.agregar_voluntario(data):
        return jsonify({'success': True})
    return jsonify({
        'success': False, 
        'message': 'Error al crear voluntario. El DNI podría estar duplicado.'
    })

@app.route('/admin/curso/nuevo', methods=['POST'])
@admin_required
def nuevo_curso():
    data = request.get_json()
    database = get_db()
    if database.agregar_curso(data):
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Error al crear curso'})

@app.route('/admin/voluntario/<int:voluntario_id>/cursos')
@admin_required
def cursos_voluntario(voluntario_id):
    database = get_db()
    cursos = database.obtener_cursos_voluntario(voluntario_id)
    return jsonify({
        'voluntario_id': voluntario_id,
        'cursos': cursos
    })

@app.route('/admin/voluntario/curso/actualizar', methods=['POST'])
@admin_required
def actualizar_curso_voluntario():
    data = request.get_json()
    database = get_db()
    if database.actualizar_curso_voluntario(
        data['voluntario_id'], 
        data['curso_id'], 
        data['estado']
    ):
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/admin/voluntario/<int:voluntario_id>', methods=['GET', 'PUT'])
@admin_required
def gestionar_voluntario(voluntario_id):
    database = get_db()
    
    if request.method == 'GET':
        voluntario = database.obtener_voluntario_por_id(voluntario_id)
        if voluntario:
            return jsonify({'success': True, 'voluntario': voluntario})
        return jsonify({'success': False, 'message': 'Voluntario no encontrado'}), 404
    
    elif request.method == 'PUT':
        data = request.get_json()
        if database.actualizar_voluntario(voluntario_id, data):
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Error al actualizar voluntario'})

@app.route('/admin/curso/<int:curso_id>', methods=['GET', 'PUT'])
@admin_required
def gestionar_curso(curso_id):
    database = get_db()
    
    if request.method == 'GET':
        curso = database.obtener_curso_por_id(curso_id)
        if curso:
            return jsonify({'success': True, 'curso': curso})
        return jsonify({'success': False, 'message': 'Curso no encontrado'}), 404
    
    elif request.method == 'PUT':
        data = request.get_json()
        if database.actualizar_curso(curso_id, data):
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Error al actualizar curso'})

@app.teardown_appcontext
def close_db(error):
    global db
    if db is not None:
        db.close()
        db = None

# Funciones auxiliares para el calendario
def get_calendar_month(year, month):
    """Obtiene el calendario para un mes específico"""
    return calendar.monthcalendar(year, month)

def es_dia_guardia(year, month, day, guardias):
    """Verifica si un día específico es día de guardia"""
    if day == 0:
        return False
    fecha = f"{year}-{month:02d}-{day:02d}"
    return any(g['fecha'] == fecha for g in guardias)

# Registrar funciones como filtros de Jinja2
@app.template_filter('calendario_mes')
def calendario_mes(year, month):
    return get_calendar_month(year, month)

@app.template_filter('format_date')
def format_date(date_str):
    meses = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
             'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return f"{date_obj.day} de {meses[date_obj.month]} de {date_obj.year}"
    except:
        return date_str

# Registrar funciones como variables globales de Jinja2
@app.context_processor
def utility_processor():
    return dict(
        es_dia_guardia=es_dia_guardia,
        enumerate=enumerate
    )

if __name__ == '__main__':
    app.run(debug=True) 