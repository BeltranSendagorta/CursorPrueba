import sys
import os

# Añade el directorio que contiene tu app al path
path = '/home/tuusuario/cruzroja'
if path not in sys.path:
    sys.path.append(path)

from app import app as application

# Configuración necesaria para la base de datos
application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/tuusuario/cruzroja/cruz_roja.db'
application.secret_key = 'tu_clave_secreta' 