import sqlite3
from datetime import datetime, timedelta
import hashlib
import os
from contextlib import contextmanager

class CruzRojaDB:
    def __init__(self, db_name='cruz_roja.db'):
        self.db_name = db_name
        self.conn = None
        self.connect()
        self.create_tables()

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            print(f"Error conectando a la base de datos: {e}")

    @contextmanager
    def get_db(self):
        try:
            if not self.conn:
                self.connect()
            yield self.conn
        except sqlite3.Error as e:
            print(f"Error de base de datos: {e}")
            raise
        finally:
            pass  # Mantenemos la conexión abierta

    def create_tables(self):
        if not self.conn:
            self.connect()
        try:
            cursor = self.conn.cursor()
            
            # Tabla de voluntarios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS voluntarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    apellidos TEXT NOT NULL,
                    dni TEXT UNIQUE NOT NULL,
                    telefono TEXT,
                    email TEXT,
                    password TEXT NOT NULL,
                    activo BOOLEAN DEFAULT 1
                )
            ''')

            # Tabla de roles
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE NOT NULL
                )
            ''')

            # Tabla de relación voluntarios-roles
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS voluntarios_roles (
                    voluntario_id INTEGER,
                    rol_id INTEGER,
                    fecha_asignacion DATE DEFAULT CURRENT_DATE,
                    FOREIGN KEY (voluntario_id) REFERENCES voluntarios (id),
                    FOREIGN KEY (rol_id) REFERENCES roles (id),
                    PRIMARY KEY (voluntario_id, rol_id)
                )
            ''')

            # Tabla de cursos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cursos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    descripcion TEXT,
                    horas INTEGER,
                    activo BOOLEAN DEFAULT 1
                )
            ''')

            # Tabla de progreso de cursos de voluntarios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS voluntarios_cursos (
                    voluntario_id INTEGER,
                    curso_id INTEGER,
                    estado TEXT CHECK(estado IN ('pendiente', 'en_progreso', 'completado')),
                    fecha_inicio DATE,
                    fecha_completado DATE,
                    FOREIGN KEY (voluntario_id) REFERENCES voluntarios (id),
                    FOREIGN KEY (curso_id) REFERENCES cursos (id),
                    PRIMARY KEY (voluntario_id, curso_id)
                )
            ''')

            # Tabla de guardias
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS guardias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    voluntario_id INTEGER,
                    fecha DATE NOT NULL,
                    turno TEXT CHECK(turno IN ('mañana', 'tarde')) NOT NULL,
                    FOREIGN KEY (voluntario_id) REFERENCES voluntarios (id)
                )
            ''')

            # Insertar roles predefinidos
            roles = ['admin', 'patron', 'marinero', 'socorrista']
            for rol in roles:
                cursor.execute('INSERT OR IGNORE INTO roles (nombre) VALUES (?)', (rol,))

            # Verificar si existe el admin
            cursor.execute('SELECT id FROM voluntarios WHERE dni = "admin"')
            admin = cursor.fetchone()
            
            if not admin:
                # Insertar admin por defecto
                cursor.execute('''
                    INSERT INTO voluntarios (dni, nombre, apellidos, password, activo)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('admin', 'Administrador', 'Sistema', 'admin123', 1))
                
                admin_id = cursor.lastrowid
                
                # Asignar rol admin
                cursor.execute('''
                    INSERT INTO voluntarios_roles (voluntario_id, rol_id)
                    SELECT ?, id FROM roles WHERE nombre = 'admin'
                ''', (admin_id,))

            self.conn.commit()

        except sqlite3.Error as e:
            print(f"Error creando las tablas: {e}")
            raise

    def close(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

    def get_connection(self):
        """Crea una nueva conexión con timeout"""
        return sqlite3.connect(self.db_name, timeout=20)

    def init_database(self):
        """Inicializa la base de datos con las tablas necesarias"""
        conn = None
        try:
            conn = self.get_connection()
            c = conn.cursor()

            # Crear tablas
            c.executescript('''
                -- Tabla de usuarios
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    nombre TEXT NOT NULL,
                    rol TEXT NOT NULL,
                    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Tabla de roles de voluntarios
                CREATE TABLE IF NOT EXISTS roles_voluntario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER,
                    tipo_rol TEXT NOT NULL,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
                    UNIQUE(usuario_id, tipo_rol)
                );

                -- Tabla de cursos
                CREATE TABLE IF NOT EXISTS cursos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    descripcion TEXT
                );

                -- Tabla de estado de cursos por voluntario
                CREATE TABLE IF NOT EXISTS cursos_voluntario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER,
                    curso_id INTEGER,
                    estado TEXT NOT NULL,
                    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
                    FOREIGN KEY (curso_id) REFERENCES cursos(id),
                    UNIQUE(usuario_id, curso_id)
                );
            ''')

            # Verificar si ya existen datos
            c.execute("SELECT COUNT(*) FROM cursos")
            if c.fetchone()[0] == 0:
                cursos_iniciales = [
                    ('Primeros Auxilios', 'Curso básico de primeros auxilios'),
                    ('Comunicaciones', 'Curso de comunicaciones marítimas'),
                    ('Navegación Básica', 'Fundamentos de navegación'),
                    ('Navegación Avanzada', 'Navegación avanzada y maniobras')
                ]
                c.executemany("INSERT INTO cursos (nombre, descripcion) VALUES (?, ?)", 
                             cursos_iniciales)

            # Verificar usuarios existentes
            c.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'admin'")
            if c.fetchone()[0] == 0:
                self._crear_usuario_inicial(c, 'admin', 'admin123', 'Administrador', 'admin')

            c.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'beltran'")
            if c.fetchone()[0] == 0:
                self._crear_usuario_inicial(c, 'beltran', 'arriluce', 'Beltrán', 'voluntario')
                
                # Asignar roles a Beltrán
                c.execute("SELECT id FROM usuarios WHERE username = 'beltran'")
                usuario_id = c.fetchone()[0]
                roles = ['patron', 'socorrista']
                for rol in roles:
                    c.execute("INSERT OR IGNORE INTO roles_voluntario (usuario_id, tipo_rol) VALUES (?, ?)",
                             (usuario_id, rol))

            conn.commit()

        except sqlite3.Error as e:
            print(f"Error en la base de datos: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def _crear_usuario_inicial(self, cursor, username, password, nombre, rol):
        """Método interno para crear usuarios iniciales"""
        hashed_password = self.hash_password(password)
        cursor.execute("""
            INSERT OR IGNORE INTO usuarios (username, password, nombre, rol)
            VALUES (?, ?, ?, ?)
        """, (username, hashed_password, nombre, rol))

    def hash_password(self, password):
        """Genera un hash de la contraseña"""
        return hashlib.sha256(password.encode()).hexdigest()

    def crear_usuario(self, username, password, nombre, rol):
        """Crea un nuevo usuario en la base de datos"""
        conn = None
        try:
            conn = self.get_connection()
            c = conn.cursor()
            c.execute("""
                INSERT INTO usuarios (username, password, nombre, rol)
                VALUES (?, ?, ?, ?)
            """, (username, self.hash_password(password), nombre, rol))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            if conn:
                conn.close()

    def verificar_usuario(self, username, password):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    v.id, 
                    v.nombre, 
                    v.apellidos,
                    v.dni,
                    GROUP_CONCAT(r.nombre) as roles
                FROM voluntarios v
                LEFT JOIN voluntarios_roles vr ON v.id = vr.voluntario_id
                LEFT JOIN roles r ON vr.rol_id = r.id
                WHERE v.dni = ? AND v.password = ? AND v.activo = 1
                GROUP BY v.id
            """, (username, password))
            
            user = cursor.fetchone()
            if user:
                roles = user['roles'].split(',') if user['roles'] else []
                return {
                    'id': user['id'],
                    'nombre': user['nombre'],
                    'apellidos': user['apellidos'],
                    'dni': user['dni'],
                    'rol': 'admin' if 'admin' in roles else 'voluntario'
                }
            return None
        except sqlite3.Error as e:
            print(f"Error al verificar usuario: {e}")
            return None

    def obtener_cursos_voluntario(self, voluntario_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT 
                    c.id,
                    c.nombre,
                    c.descripcion,
                    vc.estado,
                    vc.fecha_inicio,
                    vc.fecha_completado
                FROM cursos c
                LEFT JOIN voluntarios_cursos vc ON c.id = vc.curso_id AND vc.voluntario_id = ?
                WHERE c.activo = 1
            ''', (voluntario_id,))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error al obtener cursos del voluntario: {e}")
            return []

    def actualizar_estado_curso(self, usuario_id, curso_id, estado):
        """Actualiza el estado de un curso para un voluntario"""
        conn = None
        try:
            conn = self.get_connection()
            c = conn.cursor()
            c.execute("""
                INSERT OR REPLACE INTO cursos_voluntario (usuario_id, curso_id, estado)
                VALUES (?, ?, ?)
            """, (usuario_id, curso_id, estado))
            conn.commit()
            return True
        except:
            return False
        finally:
            if conn:
                conn.close()

    def obtener_roles_voluntario(self, usuario_id):
        """Obtiene los roles de un voluntario"""
        conn = None
        try:
            conn = self.get_connection()
            c = conn.cursor()
            c.execute("""
                SELECT tipo_rol FROM roles_voluntario
                WHERE usuario_id = ?
            """, (usuario_id,))
            roles = [row[0] for row in c.fetchall()]
            return roles
        finally:
            if conn:
                conn.close()

    def actualizar_roles_voluntario(self, usuario_id, roles):
        """Actualiza los roles de un voluntario"""
        conn = None
        try:
            conn = self.get_connection()
            c = conn.cursor()
            try:
                # Eliminar roles actuales
                c.execute("DELETE FROM roles_voluntario WHERE usuario_id = ?", (usuario_id,))
                # Insertar nuevos roles
                for rol in roles:
                    c.execute("""
                        INSERT INTO roles_voluntario (usuario_id, tipo_rol)
                        VALUES (?, ?)
                    """, (usuario_id, rol))
                conn.commit()
                return True
            except:
                conn.rollback()
                return False
        except:
            raise
        finally:
            if conn:
                conn.close()

    def obtener_datos_voluntario(self, user_id):
        try:
            cursor = self.conn.cursor()
            # Obtener datos básicos del voluntario
            cursor.execute("""
                SELECT 
                    v.id,
                    v.nombre,
                    v.apellidos,
                    v.dni,
                    v.telefono,
                    v.email,
                    GROUP_CONCAT(r.nombre) as roles
                FROM voluntarios v
                LEFT JOIN voluntarios_roles vr ON v.id = vr.voluntario_id
                LEFT JOIN roles r ON vr.rol_id = r.id
                WHERE v.id = ? AND v.activo = 1
                GROUP BY v.id
            """, (user_id,))
            
            voluntario = cursor.fetchone()
            if voluntario:
                # Convertir a diccionario con nombres de columnas
                return {
                    'id': voluntario[0],
                    'nombre': voluntario[1],
                    'apellidos': voluntario[2],
                    'dni': voluntario[3],
                    'telefono': voluntario[4] or '',
                    'email': voluntario[5] or '',
                    'roles': voluntario[6].split(',') if voluntario[6] else []
                }
            return None
        except sqlite3.Error as e:
            print(f"Error al obtener datos del voluntario: {e}")
            return None

    def obtener_voluntarios(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT 
                    v.id, 
                    v.nombre, 
                    v.apellidos, 
                    v.dni, 
                    v.telefono, 
                    v.email,
                    GROUP_CONCAT(r.nombre) as roles
                FROM voluntarios v
                LEFT JOIN voluntarios_roles vr ON v.id = vr.voluntario_id
                LEFT JOIN roles r ON vr.rol_id = r.id
                WHERE v.dni != 'admin' AND v.activo = 1
                GROUP BY v.id, v.nombre, v.apellidos, v.dni, v.telefono, v.email
            ''')
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error al obtener voluntarios: {e}")
            return []

    def agregar_voluntario(self, datos):
        try:
            cursor = self.conn.cursor()
            
            # Primero insertamos el voluntario
            cursor.execute('''
                INSERT INTO voluntarios (nombre, apellidos, dni, telefono, email, password)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                datos['nombre'],
                datos['apellidos'],
                datos['dni'],
                datos.get('telefono', ''),
                datos.get('email', ''),
                datos['password']
            ))
            
            voluntario_id = cursor.lastrowid
            
            # Luego asignamos los roles
            if 'roles' in datos and datos['roles']:
                for rol in datos['roles']:
                    cursor.execute('''
                        INSERT INTO voluntarios_roles (voluntario_id, rol_id)
                        SELECT ?, id FROM roles WHERE nombre = ?
                    ''', (voluntario_id, rol))
            
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error al agregar voluntario: {e}")
            self.conn.rollback()
            return False

    def obtener_roles(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM roles WHERE nombre != "admin"')
            return [dict(r) for r in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error al obtener roles: {e}")
            return []

    def agregar_curso(self, datos):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO cursos (nombre, descripcion, horas)
                VALUES (?, ?, ?)
            ''', (datos['nombre'], datos['descripcion'], datos['horas']))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error al agregar curso: {e}")
            return False

    def obtener_cursos(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM cursos')
            return [dict(c) for c in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error al obtener cursos: {e}")
            return []

    def actualizar_curso_voluntario(self, voluntario_id, curso_id, estado):
        try:
            cursor = self.conn.cursor()
            fecha = None if estado != 'completado' else 'CURRENT_DATE'
            cursor.execute('''
                INSERT OR REPLACE INTO voluntarios_cursos 
                (voluntario_id, curso_id, estado, fecha_completado)
                VALUES (?, ?, ?, ?)
            ''', (voluntario_id, curso_id, estado, fecha))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error al actualizar curso del voluntario: {e}")
            return False

    def obtener_voluntario_por_id(self, voluntario_id):
        try:
            cursor = self.conn.cursor()
            # Primero obtenemos los datos básicos del voluntario
            cursor.execute('''
                SELECT 
                    id, 
                    nombre, 
                    apellidos, 
                    dni, 
                    telefono, 
                    email
                FROM voluntarios 
                WHERE id = ? AND activo = 1
            ''', (voluntario_id,))
            
            voluntario = cursor.fetchone()
            
            if voluntario:
                # Convertimos a diccionario
                resultado = {
                    'id': voluntario[0],
                    'nombre': voluntario[1],
                    'apellidos': voluntario[2],
                    'dni': voluntario[3],
                    'telefono': voluntario[4] or '',
                    'email': voluntario[5] or ''
                }
                
                # Obtenemos los roles del voluntario
                cursor.execute('''
                    SELECT r.nombre
                    FROM roles r
                    JOIN voluntarios_roles vr ON r.id = vr.rol_id
                    WHERE vr.voluntario_id = ?
                ''', (voluntario_id,))
                
                roles = cursor.fetchall()
                resultado['roles'] = [rol[0] for rol in roles]
                
                return resultado
            return None
        except sqlite3.Error as e:
            print(f"Error al obtener voluntario: {e}")
            return None

    def actualizar_voluntario(self, voluntario_id, datos):
        try:
            cursor = self.conn.cursor()
            
            # Actualizar datos básicos del voluntario
            cursor.execute('''
                UPDATE voluntarios 
                SET nombre = ?, 
                    apellidos = ?, 
                    telefono = ?, 
                    email = ?
                WHERE id = ?
            ''', (
                datos['nombre'],
                datos['apellidos'],
                datos.get('telefono', ''),
                datos.get('email', ''),
                voluntario_id
            ))

            # Si se proporciona nueva contraseña, actualizarla
            if 'password' in datos and datos['password'].strip():
                cursor.execute('''
                    UPDATE voluntarios 
                    SET password = ?
                    WHERE id = ?
                ''', (datos['password'], voluntario_id))

            # Actualizar roles si se proporcionan
            if 'roles' in datos:
                # Eliminar roles actuales
                cursor.execute('DELETE FROM voluntarios_roles WHERE voluntario_id = ?', (voluntario_id,))
                
                # Insertar nuevos roles
                for rol in datos['roles']:
                    cursor.execute('''
                        INSERT INTO voluntarios_roles (voluntario_id, rol_id)
                        SELECT ?, id FROM roles WHERE nombre = ?
                    ''', (voluntario_id, rol))

            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error al actualizar voluntario: {e}")
            self.conn.rollback()
            return False

    def obtener_curso_por_id(self, curso_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT id, nombre, descripcion, horas
                FROM cursos
                WHERE id = ? AND activo = 1
            ''', (curso_id,))
            curso = cursor.fetchone()
            return dict(curso) if curso else None
        except sqlite3.Error as e:
            print(f"Error al obtener curso: {e}")
            return None

    def actualizar_curso(self, curso_id, datos):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE cursos 
                SET nombre = ?, 
                    descripcion = ?, 
                    horas = ?
                WHERE id = ? AND activo = 1
            ''', (
                datos['nombre'],
                datos['descripcion'],
                datos['horas'],
                curso_id
            ))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error al actualizar curso: {e}")
            self.conn.rollback()
            return False

    def calcular_guardias_año(self, fecha_inicio='2025-03-14'):
        """Calcula todas las guardias del año a partir de una fecha base"""
        try:
            # Convertir la fecha inicial a datetime
            fecha_actual = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            guardias = []
            
            # Mientras estemos en el mismo año
            while fecha_actual.year == 2025:
                # Agregar el fin de semana de guardia (viernes, sábado y domingo)
                for i in range(3):
                    fecha_guardia = fecha_actual + timedelta(days=i)
                    if fecha_guardia.year == 2025:
                        guardias.append(fecha_guardia.strftime('%Y-%m-%d'))
                
                # Avanzar 4 semanas (28 días) para la siguiente guardia
                fecha_actual += timedelta(days=28)
            
            return guardias
        except Exception as e:
            print(f"Error calculando guardias: {e}")
            return []

    def generar_guardias_voluntario(self, voluntario_id):
        """Genera las guardias para un voluntario"""
        try:
            cursor = self.conn.cursor()
            
            # Limpiar guardias existentes
            cursor.execute('DELETE FROM guardias WHERE voluntario_id = ?', (voluntario_id,))
            
            # Obtener las fechas de guardia
            fechas_guardia = self.calcular_guardias_año()
            
            # Insertar las nuevas guardias
            for fecha in fechas_guardia:
                cursor.execute('''
                    INSERT INTO guardias (voluntario_id, fecha, turno)
                    VALUES (?, ?, ?)
                ''', (voluntario_id, fecha, 'completo'))
            
            self.conn.commit()
            print(f"Guardias generadas para voluntario {voluntario_id}: {fechas_guardia}")
            return True
        except sqlite3.Error as e:
            print(f"Error al generar guardias: {e}")
            self.conn.rollback()
            return False

    def obtener_guardias_por_año(self, voluntario_id, año):
        """Obtiene todas las guardias de un voluntario para un año específico"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT fecha
                FROM guardias 
                WHERE voluntario_id = ? 
                AND strftime('%Y', fecha) = ?
                ORDER BY fecha ASC
            ''', (voluntario_id, str(año)))
            
            return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"Error al obtener guardias por año: {e}")
            return []

    def obtener_proxima_guardia(self, voluntario_id):
        """Obtiene la próxima guardia del voluntario"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT fecha, turno
                FROM guardias 
                WHERE voluntario_id = ? 
                AND fecha >= DATE('now')
                ORDER BY fecha ASC
                LIMIT 1
            ''', (voluntario_id,))
            
            guardia = cursor.fetchone()
            if guardia:
                fecha = datetime.strptime(guardia[0], '%Y-%m-%d')
                return {
                    'fecha': guardia[0],
                    'fecha_formateada': fecha.strftime('%d de %B de %Y'),
                    'turno': guardia[1]
                }
            return None
        except sqlite3.Error as e:
            print(f"Error al obtener próxima guardia: {e}")
            return None

    def calcular_guardias_futuras(self, fecha_inicio, fecha_fin):
        """Calcula las guardias entre dos fechas basándose en el patrón de 4 semanas"""
        try:
            # Fecha base conocida del Grupo 3 (primer viernes de guardia en 2025)
            fecha_base = datetime(2025, 1, 17)  # 17 de enero de 2025
            
            # Convertir fechas de entrada a datetime
            inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
            
            guardias = []
            
            # Encontrar la primera guardia después de la fecha de inicio
            dias_diff = (inicio - fecha_base).days
            semanas_diff = dias_diff // 7
            semanas_ajuste = semanas_diff - (semanas_diff % 4)
            primera_guardia = fecha_base + timedelta(weeks=semanas_ajuste)
            
            # Si la primera guardia calculada es anterior a la fecha de inicio,
            # avanzamos al siguiente ciclo de 4 semanas
            if primera_guardia < inicio:
                primera_guardia += timedelta(weeks=4)
            
            # Generar todas las guardias hasta la fecha fin
            fecha_actual = primera_guardia
            while fecha_actual <= fin:
                # Cada guardia dura 3 días (viernes, sábado y domingo)
                for i in range(3):
                    fecha_guardia = fecha_actual + timedelta(days=i)
                    if inicio <= fecha_guardia <= fin:
                        guardias.append(fecha_guardia.strftime('%Y-%m-%d'))
                
                # Avanzar 4 semanas hasta la siguiente guardia
                fecha_actual += timedelta(weeks=4)
            
            return guardias
        except Exception as e:
            print(f"Error calculando guardias futuras: {e}")
            return []

    def generar_guardias_grupo3(self, voluntario_id):
        try:
            cursor = self.conn.cursor()
            # Fechas de guardia para el Grupo 3 en 2025
            fechas_guardia = [
                # Enero
                '2025-01-17', '2025-01-18', '2025-01-19',
                # Febrero
                '2025-02-14', '2025-02-15', '2025-02-16',
                # Marzo
                '2025-03-14', '2025-03-15', '2025-03-16',
                # Abril
                '2025-04-11', '2025-04-12', '2025-04-13',
                # Mayo
                '2025-05-09', '2025-05-10', '2025-05-11',
                # Junio
                '2025-06-06', '2025-06-07', '2025-06-08',
                # Julio
                '2025-07-04', '2025-07-05', '2025-07-06',
                # Agosto
                '2025-08-01', '2025-08-02', '2025-08-03',
                '2025-08-29', '2025-08-30', '2025-08-31',
                # Septiembre
                '2025-09-26', '2025-09-27', '2025-09-28',
                # Octubre
                '2025-10-24', '2025-10-25', '2025-10-26',
                # Noviembre
                '2025-11-21', '2025-11-22', '2025-11-23',
                # Diciembre
                '2025-12-19', '2025-12-20', '2025-12-21'
            ]
            
            # Limpiar guardias existentes para este voluntario
            cursor.execute('DELETE FROM guardias WHERE voluntario_id = ?', (voluntario_id,))
            
            # Insertar las nuevas guardias
            for fecha in fechas_guardia:
                cursor.execute('''
                    INSERT INTO guardias (voluntario_id, fecha, turno)
                    VALUES (?, ?, ?)
                ''', (voluntario_id, fecha, 'completo'))
            
            self.conn.commit()
            print(f"Guardias generadas para voluntario {voluntario_id}")
            return True
        except sqlite3.Error as e:
            print(f"Error al generar guardias: {e}")
            self.conn.rollback()
            return False

# Ejemplo de uso
if __name__ == "__main__":
    db = CruzRojaDB()
    print("Base de datos inicializada correctamente")
    
    # Probar login
    usuario = db.verificar_usuario('beltran', 'arriluce')
    if usuario:
        print(f"Usuario verificado: {usuario}")
        
        # Obtener roles
        roles = db.obtener_roles_voluntario(usuario['id'])
        print(f"Roles: {roles}")
        
        # Obtener cursos
        cursos = db.obtener_cursos_voluntario(usuario['id'])
        print(f"Cursos: {cursos}")

    # Probar generar guardias
    if db.generar_guardias_grupo3(usuario['id']):
        print("Guardias generadas correctamente")
    else:
        print("Error al generar guardias")

    # Obtener guardias por año
    guardias_por_año = db.obtener_guardias_por_año(usuario['id'], 2025)
    print(f"Guardias por año: {guardias_por_año}") 