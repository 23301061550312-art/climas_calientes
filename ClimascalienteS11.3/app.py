from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import os
import schedule
import time
from threading import Thread
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'clave-temporal-desarrollo')

GLOBAL_API_KEY = os.environ.get('API_KEY', '3088449fddf506256fc39e7e40d88ec4')

# Configuración para desarrollo local (MySQL)
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'database': os.environ.get('DB_NAME', 'formulario_bd')
}

def obtener_conexion():
    # Si estamos en producción (Render con PostgreSQL)
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        try:
            # Para PostgreSQL en producción
            url = urlparse(database_url)
            conn = psycopg2.connect(
                database=url.path[1:],  # Elimina el / inicial
                user=url.username,
                password=url.password,
                host=url.hostname,
                port=url.port
            )
            return conn
        except Exception as e:
            print(f"Error conectando a PostgreSQL: {e}")
            # Fallback a MySQL local
            try:
                return mysql.connector.connect(**DB_CONFIG)
            except Exception as e2:
                print(f"Error también con MySQL: {e2}")
                return None
    else:
        # Para MySQL local en desarrollo
        try:
            return mysql.connector.connect(**DB_CONFIG)
        except Exception as e:
            print(f"Error conectando a MySQL local: {e}")
            return None

# ----------------------------------------------------
# FUNCIONES DE INICIALIZACIÓN DE USUARIOS
# ----------------------------------------------------
def actualizar_contraseñas():
    """Actualiza contraseñas de usuarios existentes"""
    print("🔧 Actualizando contraseñas de usuarios...")
    
    conexion = obtener_conexion()
    if conexion is None:
        print("❌ Error: No se pudo conectar a la base de datos")
        return
        
    cursor = conexion.cursor(dictionary=True)
    
    # Lista de usuarios a actualizar
    usuarios = [
        {'username': 'admin', 'password': '123456'},
        {'username': 'superadmin', 'password': '123456'},
        {'username': 'demo', 'password': '123456'},
        {'username': 'usuario1', 'password': '123456'}
    ]
    
    usuarios_actualizados = 0
    
    for usuario in usuarios:
        try:
            # Generar hash correcto de la contraseña
            password_hash = generate_password_hash(usuario['password'])
            
            # Verificar si el usuario existe
            cursor.execute('SELECT id FROM usuarios WHERE username = %s', (usuario['username'],))
            usuario_existente = cursor.fetchone()
            
            if usuario_existente:
                # Actualizar en la base de datos
                cursor.execute('UPDATE usuarios SET password = %s WHERE username = %s', 
                              (password_hash, usuario['username']))
                usuarios_actualizados += 1
                print(f"✓ Contraseña actualizada para: {usuario['username']} -> {usuario['password']}")
            else:
                print(f"⚠ Usuario no encontrado: {usuario['username']}")
                
        except Exception as e:
            print(f"❌ Error actualizando usuario {usuario['username']}: {e}")
    
    conexion.commit()
    cursor.close()
    conexion.close()
    
    print(f"\n¡Se actualizaron {usuarios_actualizados} contraseñas!")
    if usuarios_actualizados > 0:
        print("Ahora puedes iniciar sesión con:")
        for usuario in usuarios:
            print(f"Usuario: {usuario['username']} | Contraseña: {usuario['password']}")

def crear_usuarios_iniciales():
    """Crea usuarios iniciales en el sistema"""
    print("👥 Creando usuarios iniciales...")
    
    conexion = obtener_conexion()
    if conexion is None:
        print("❌ Error: No se pudo conectar a la base de datos")
        return
        
    cursor = conexion.cursor()
    
    try:
        # Verificar si ya existen usuarios para no duplicar
        cursor.execute('SELECT COUNT(*) as count FROM usuarios')
        resultado = cursor.fetchone()
        count_usuarios = resultado[0] if resultado else 0
        
        if count_usuarios > 0:
            print(f"ℹ Ya existen {count_usuarios} usuarios en la base de datos")
            cursor.close()
            conexion.close()
            return
        
        # Limpiar tabla primero (solo si está vacía)
        cursor.execute('DELETE FROM usuarios')
        
        # Usuarios con contraseñas REALES
        usuarios = [
            # ADMINS
            ('admin', 'admin@sistema.com', 'admin123', 'admin'),
            ('superuser', 'super@empresa.com', 'Super2024!', 'admin'),
            ('administrador', 'admin@aguascalientes.com', 'AdminAgs123', 'admin'),
            
            # USUARIOS NORMALES
            ('juanperez', 'juan@correo.com', 'JuanPassword1', 'user'),
            ('mariagarcia', 'maria@correo.com', 'MariaSecure2', 'user'),
            ('carloslopez', 'carlos@correo.com', 'CarlosPass3', 'user'),
            ('anatorres', 'ana@correo.com', 'AnaClave456', 'user'),
            ('robertosmith', 'roberto@correo.com', 'Robert789', 'user')
        ]
        
        usuarios_creados = 0
        
        for username, email, password, rol in usuarios:
            try:
                # Generar hash REAL de la contraseña
                password_hash = generate_password_hash(password)
                
                # Insertar usuario
                cursor.execute(
                    'INSERT INTO usuarios (username, email, password, rol) VALUES (%s, %s, %s, %s)',
                    (username, email, password_hash, rol)
                )
                usuarios_creados += 1
                print(f"✅ Usuario creado: {username} | Contraseña: {password} | Rol: {rol}")
                
            except Exception as e:
                print(f"❌ Error creando usuario {username}: {e}")
        
        conexion.commit()
        
        print("\n" + "="*50)
        print(f"🎯 {usuarios_creados} USUARIOS CREADOS EXITOSAMENTE")
        print("="*50)
        print("\n🔐 ADMINS (pueden configurar API y ver CRUD):")
        print("   admin / admin123")
        print("   superuser / Super2024!")
        print("   administrador / AdminAgs123")
        
        print("\n👥 USUARIOS NORMALES (solo ven clima):")
        print("   juanperez / JuanPassword1")
        print("   mariagarcia / MariaSecure2")
        print("   carloslopez / CarlosPass3")
        print("   anatorres / AnaClave456")
        print("   robertosmith / Robert789")
        
        print("\n📍 URL: http://localhost:5000/login")
        
    except Exception as e:
        print(f"❌ Error general al crear usuarios: {e}")
    finally:
        cursor.close()
        conexion.close()

def inicializar_sistema():
    """Función que se ejecuta al iniciar la aplicación"""
    print("\n" + "="*60)
    print("🚀 INICIALIZANDO SISTEMA DE CLIMA Y EMERGENCIAS")
    print("="*60)
    
    # Crear usuarios iniciales
    crear_usuarios_iniciales()
    
    # Actualizar contraseñas existentes
    actualizar_contraseñas()
    
    print("\n✅ Inicialización completada")
    print("="*60 + "\n")

# ----------------------------------------------------
# RUTAS PRINCIPALES MODIFICADAS
# ----------------------------------------------------
@app.route('/')
def inicio():
    """Página principal con información institucional"""
    return render_template('inicio.html')

# ----------------------------------------------------
# RUTAS DE AUTENTICACIÓN
# ----------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('clima'))
   
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
       
        conexion = obtener_conexion()
        if conexion is None:
            flash('Error de conexión a la base de datos', 'error')
            return render_template('login.html')
           
        cursor = conexion.cursor(dictionary=True)
        cursor.execute('SELECT * FROM usuarios WHERE username = %s', (username,))
        usuario = cursor.fetchone()
        cursor.close()
        conexion.close()
       
        if usuario and check_password_hash(usuario['password'], password):
            session['user_id'] = usuario['id']
            session['username'] = usuario['username']
            session['rol'] = usuario['rol']
            flash('¡Inicio de sesión exitoso!', 'success')
            return redirect(url_for('clima'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
   
    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if 'user_id' in session:
        return redirect(url_for('clima'))
   
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
       
        # VALIDACIÓN DE CONTRASEÑAS
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('registro.html')
        
        # VALIDACIÓN DE USERNAME (solo letras)
        if not username.replace(' ', '').isalpha():
            flash('El usuario solo puede contener letras y espacios', 'error')
            return render_template('registro.html')
        
        # VALIDACIÓN DE EMAIL (solo verificar que tenga @)
        if '@' not in email:
            flash('El email debe contener @', 'error')
            return render_template('registro.html')
       
        conexion = obtener_conexion()
        if conexion is None:
            flash('Error de conexión a la base de datos', 'error')
            return render_template('registro.html')
           
        cursor = conexion.cursor(dictionary=True)
        cursor.execute('SELECT id FROM usuarios WHERE username = %s OR email = %s', (username, email))
        usuario_existente = cursor.fetchone()
       
        if usuario_existente:
            flash('El usuario o email ya están registrados', 'error')
            cursor.close()
            conexion.close()
            return render_template('registro.html')
       
        hashed_password = generate_password_hash(password)
        cursor.execute('INSERT INTO usuarios (username, email, password, rol) VALUES (%s, %s, %s, %s)',
                      (username, email, hashed_password, 'user'))
        conexion.commit()
        cursor.close()
        conexion.close()
       
        flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))
   
    return render_template('registro.html')

# ----------------------------------------------------
# RUTAS DEL SISTEMA DE CLIMA (PROTEGIDAS)
# ----------------------------------------------------
@app.route('/clima')
def clima():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para acceder al clima', 'error')
        return redirect(url_for('login'))
    return render_template('clima.html', username=session['username'], rol=session.get('rol'))

@app.route('/api/weather')
def get_weather():
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
   
    api_key = GLOBAL_API_KEY
   
    locations = [
        {'city': 'Aguascalientes', 'state': 'Ags', 'country': 'MX'},
        {'city': 'Aguascalientes', 'state': '', 'country': 'MX'},
        {'lat': 21.8853, 'lon': -102.2916}
    ]
   
    for location in locations:
        try:
            if 'lat' in location and 'lon' in location:
                url = f'https://api.openweathermap.org/data/2.5/weather?lat={location["lat"]}&lon={location["lon"]}&appid={api_key}&units=metric&lang=es'
            else:
                url = f'https://api.openweathermap.org/data/2.5/weather?q={location["city"]},{location["country"]}&appid={api_key}&units=metric&lang=es'
           
            response = requests.get(url, timeout=10)
           
            if response.status_code == 200:
                data = response.json()
                city_name = data.get('name', '').lower()
                country = data.get('sys', {}).get('country', '')
               
                if ('aguascalientes' in city_name or 'ags' in city_name) and country == 'MX':
                    weather_data = {
                        'temperature': round(data['main']['temp']),
                        'feels_like': round(data['main']['feels_like']),
                        'humidity': data['main']['humidity'],
                        'pressure': data['main']['pressure'],
                        'wind_speed': round(data['wind']['speed'] * 3.6),
                        'description': data['weather'][0]['description'].capitalize(),
                        'icon': data['weather'][0]['icon'],
                        'city': data['name'],
                        'country': data['sys']['country'],
                        'source': 'OpenWeatherMap'
                    }
                    return jsonify(weather_data)
           
        except requests.exceptions.RequestException:
            continue
   
    return jsonify({
        'temperature': 22,
        'feels_like': 24,
        'humidity': 45,
        'pressure': 1013,
        'wind_speed': 12,
        'description': 'Despejado',
        'icon': '01d',
        'city': 'Aguascalientes',
        'country': 'MX',
        'source': 'Datos de ejemplo'
    })

# ----------------------------------------------------
# RUTAS ADMINISTRATIVAS
# ----------------------------------------------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('rol') != 'admin':
        flash('No tienes permisos para acceder a esta sección', 'error')
        return redirect(url_for('inicio'))
   
    conexion = obtener_conexion()
    if conexion is None:
        flash('Error de conexión a la base de datos', 'error')
        return redirect(url_for('inicio'))
       
    cursor = conexion.cursor(dictionary=True)
    busqueda = request.args.get('busqueda', '')
   
    if busqueda:
        try:
            # Convertir a número para buscar por ID exacto
            usuario_id = int(busqueda)
            cursor.execute('''
                SELECT * FROM usuarios
                WHERE id = %s
                ORDER BY id DESC
            ''', (usuario_id,))
        except ValueError:
            # Si no es un número, no mostrar resultados
            cursor.execute('SELECT * FROM usuarios WHERE 1=0')
    else:
        cursor.execute('SELECT * FROM usuarios ORDER BY id DESC')
   
    usuarios = cursor.fetchall()
    cursor.close()
    conexion.close()
   
    return render_template('admin.html',
                         usuarios=usuarios,
                         username=session['username'],
                         busqueda=busqueda)

@app.route('/eliminar_usuario/<int:usuario_id>')
def eliminar_usuario(usuario_id):
    if 'user_id' not in session or session.get('rol') != 'admin':
        flash('No tienes permisos para realizar esta acción', 'error')
        return redirect(url_for('inicio'))
   
    if usuario_id == session['user_id']:
        flash('No puedes eliminar tu propio usuario', 'error')
        return redirect(url_for('dashboard'))
   
    conexion = obtener_conexion()
    if conexion is None:
        flash('Error de conexión a la base de datos', 'error')
        return redirect(url_for('dashboard'))
       
    cursor = conexion.cursor()
   
    try:
        cursor.execute('DELETE FROM usuarios WHERE id = %s', (usuario_id,))
        conexion.commit()
        flash('Usuario eliminado correctamente', 'success')
    except Exception as e:
        flash('Error al eliminar el usuario', 'error')
   
    cursor.close()
    conexion.close()
    return redirect(url_for('dashboard'))

@app.route('/editar_usuario/<int:usuario_id>', methods=['GET', 'POST'])
def editar_usuario(usuario_id):
    if 'user_id' not in session or session.get('rol') != 'admin':
        flash('No tienes permisos para realizar esta acción', 'error')
        return redirect(url_for('inicio'))
   
    conexion = obtener_conexion()
    if conexion is None:
        flash('Error de conexión a la base de datos', 'error')
        return redirect(url_for('dashboard'))
       
    cursor = conexion.cursor(dictionary=True)
   
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        rol = request.form['rol']
        nueva_password = request.form.get('nueva_password', '')
       
        try:
            if nueva_password:
                hashed_password = generate_password_hash(nueva_password)
                cursor.execute('''
                    UPDATE usuarios
                    SET username = %s, email = %s, rol = %s, password = %s
                    WHERE id = %s
                ''', (username, email, rol, hashed_password, usuario_id))
            else:
                cursor.execute('''
                    UPDATE usuarios
                    SET username = %s, email = %s, rol = %s
                    WHERE id = %s
                ''', (username, email, rol, usuario_id))
           
            conexion.commit()
            flash('Usuario actualizado correctamente', 'success')
           
        except Exception as e:
            flash('Error al actualizar el usuario', 'error')
       
        cursor.close()
        conexion.close()
        return redirect(url_for('dashboard'))
   
    cursor.execute('SELECT * FROM usuarios WHERE id = %s', (usuario_id,))
    usuario = cursor.fetchone()
    cursor.close()
    conexion.close()
   
    if not usuario:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('dashboard'))
   
    return render_template('editar_usuario.html',
                         usuario=usuario,
                         username=session['username'])

@app.route('/crear_usuario', methods=['GET', 'POST'])
def crear_usuario():
    if 'user_id' not in session or session.get('rol') != 'admin':
        flash('No tienes permisos para realizar esta acción', 'error')
        return redirect(url_for('inicio'))
   
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        rol = request.form['rol']
       
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('crear_usuario.html', username=session['username'])
       
        conexion = obtener_conexion()
        if conexion is None:
            flash('Error de conexión a la base de datos', 'error')
            return render_template('crear_usuario.html', username=session['username'])
           
        cursor = conexion.cursor(dictionary=True)
       
        cursor.execute('SELECT id FROM usuarios WHERE username = %s OR email = %s', (username, email))
        usuario_existente = cursor.fetchone()
       
        if usuario_existente:
            flash('El usuario o email ya están registrados', 'error')
            cursor.close()
            conexion.close()
            return render_template('crear_usuario.html', username=session['username'])
       
        hashed_password = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO usuarios (username, email, password, rol)
            VALUES (%s, %s, %s, %s)
        ''', (username, email, hashed_password, rol))
       
        conexion.commit()
        cursor.close()
        conexion.close()
       
        flash('Usuario creado correctamente', 'success')
        return redirect(url_for('dashboard'))
   
    return render_template('crear_usuario.html', username=session['username'])

# ----------------------------------------------------
# RUTAS PARA ADMINISTRACIÓN DE NÚMEROS DE EMERGENCIA
# ----------------------------------------------------

@app.route('/admin/emergencia')
def admin_emergencia():
    if 'user_id' not in session or session.get('rol') != 'admin':
        flash('No tienes permisos para acceder a esta sección', 'error')
        return redirect(url_for('inicio'))
   
    conexion = obtener_conexion()
    if conexion is None:
        flash('Error de conexión a la base de datos', 'error')
        return redirect(url_for('inicio'))
       
    cursor = conexion.cursor(dictionary=True)
    
    # Obtener todos los números de emergencia
    cursor.execute('SELECT * FROM numeros_emergencia ORDER BY categoria, nombre')
    numeros = cursor.fetchall()
    cursor.close()
    conexion.close()
   
    return render_template('admin_emergencia.html',
                         numeros=numeros,
                         username=session['username'])

@app.route('/admin/emergencia/agregar', methods=['GET', 'POST'])
def agregar_emergencia():
    if 'user_id' not in session or session.get('rol') != 'admin':
        flash('No tienes permisos para realizar esta acción', 'error')
        return redirect(url_for('inicio'))
   
    if request.method == 'POST':
        nombre = request.form['nombre']
        numero = request.form['numero']
        descripcion = request.form['descripcion']
        icono = request.form['icono']
        categoria = request.form['categoria']
        badge = request.form.get('badge', '')
       
        conexion = obtener_conexion()
        if conexion is None:
            flash('Error de conexión a la base de datos', 'error')
            return redirect(url_for('admin_emergencia'))
           
        cursor = conexion.cursor()
       
        try:
            cursor.execute('''
                INSERT INTO numeros_emergencia (nombre, numero, descripcion, icono, categoria, badge)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (nombre, numero, descripcion, icono, categoria, badge))
           
            conexion.commit()
            flash('Número de emergencia agregado correctamente', 'success')
           
        except Exception as e:
            flash('Error al agregar el número de emergencia', 'error')
       
        cursor.close()
        conexion.close()
        return redirect(url_for('admin_emergencia'))
   
    return render_template('agregar_emergencia.html', username=session['username'])

@app.route('/admin/emergencia/editar/<int:numero_id>', methods=['GET', 'POST'])
def editar_emergencia(numero_id):
    if 'user_id' not in session or session.get('rol') != 'admin':
        flash('No tienes permisos para realizar esta acción', 'error')
        return redirect(url_for('inicio'))
   
    conexion = obtener_conexion()
    if conexion is None:
        flash('Error de conexión a la base de datos', 'error')
        return redirect(url_for('admin_emergencia'))
       
    cursor = conexion.cursor(dictionary=True)
   
    if request.method == 'POST':
        nombre = request.form['nombre']
        numero = request.form['numero']
        descripcion = request.form['descripcion']
        icono = request.form['icono']
        categoria = request.form['categoria']
        badge = request.form.get('badge', '')
        activo = request.form.get('activo', 0)
       
        try:
            cursor.execute('''
                UPDATE numeros_emergencia
                SET nombre = %s, numero = %s, descripcion = %s, icono = %s, categoria = %s, badge = %s, activo = %s
                WHERE id = %s
            ''', (nombre, numero, descripcion, icono, categoria, badge, activo, numero_id))
           
            conexion.commit()
            flash('Número de emergencia actualizado correctamente', 'success')
           
        except Exception as e:
            flash('Error al actualizar el número de emergencia', 'error')
       
        cursor.close()
        conexion.close()
        return redirect(url_for('admin_emergencia'))
   
    cursor.execute('SELECT * FROM numeros_emergencia WHERE id = %s', (numero_id,))
    numero_emergencia = cursor.fetchone()
    cursor.close()
    conexion.close()
   
    if not numero_emergencia:
        flash('Número de emergencia no encontrado', 'error')
        return redirect(url_for('admin_emergencia'))
   
    return render_template('editar_emergencia.html',
                         numero=numero_emergencia,
                         username=session['username'])

@app.route('/admin/emergencia/eliminar/<int:numero_id>')
def eliminar_emergencia(numero_id):
    if 'user_id' not in session or session.get('rol') != 'admin':
        flash('No tienes permisos para realizar esta acción', 'error')
        return redirect(url_for('inicio'))
   
    conexion = obtener_conexion()
    if conexion is None:
        flash('Error de conexión a la base de datos', 'error')
        return redirect(url_for('admin_emergencia'))
       
    cursor = conexion.cursor()
   
    try:
        cursor.execute('DELETE FROM numeros_emergencia WHERE id = %s', (numero_id,))
        conexion.commit()
        flash('Número de emergencia eliminado correctamente', 'success')
    except Exception as e:
        flash('Error al eliminar el número de emergencia', 'error')
   
    cursor.close()
    conexion.close()
    return redirect(url_for('admin_emergencia'))

# Ruta para obtener números de emergencia (API)
@app.route('/api/emergencia')
def get_emergencia():
    conexion = obtener_conexion()
    if conexion is None:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
    cursor = conexion.cursor(dictionary=True)
    cursor.execute('SELECT * FROM numeros_emergencia WHERE activo = TRUE ORDER BY categoria, nombre')
    numeros = cursor.fetchall()
    cursor.close()
    conexion.close()
    return jsonify(numeros)

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('inicio'))

# ----------------------------------------------------
# RUTAS PARA ADMINISTRACIÓN DE CONSEJOS
# ----------------------------------------------------

@app.route('/admin/consejos')
def admin_consejos():
    if 'user_id' not in session or session.get('rol') != 'admin':
        flash('No tienes permisos para acceder a esta sección', 'error')
        return redirect(url_for('inicio'))
   
    conexion = obtener_conexion()
    if conexion is None:
        flash('Error de conexión a la base de datos', 'error')
        return redirect(url_for('inicio'))
       
    cursor = conexion.cursor(dictionary=True)
    
    # Obtener todos los consejos
    cursor.execute('SELECT * FROM consejos_clima ORDER BY fecha_creacion DESC')
    consejos = cursor.fetchall()
    cursor.close()
    conexion.close()
   
    return render_template('admin_consejos.html',
                         consejos=consejos,
                         username=session['username'])

@app.route('/admin/consejos/agregar', methods=['GET', 'POST'])
def agregar_consejo():
    if 'user_id' not in session or session.get('rol') != 'admin':
        flash('No tienes permisos para realizar esta acción', 'error')
        return redirect(url_for('inicio'))
   
    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        icono = request.form['icono']
        etiquetas = request.form.get('etiquetas', '')
       
        conexion = obtener_conexion()
        if conexion is None:
            flash('Error de conexión a la base de datos', 'error')
            return redirect(url_for('admin_consejos'))
           
        cursor = conexion.cursor()
       
        try:
            cursor.execute('''
                INSERT INTO consejos_clima (titulo, descripcion, icono, etiquetas)
                VALUES (%s, %s, %s, %s)
            ''', (titulo, descripcion, icono, etiquetas))
           
            conexion.commit()
            flash('Consejo agregado correctamente', 'success')
           
        except Exception as e:
            flash('Error al agregar el consejo', 'error')
       
        cursor.close()
        conexion.close()
        return redirect(url_for('admin_consejos'))
   
    return render_template('agregar_consejo.html', username=session['username'])

@app.route('/admin/consejos/editar/<int:consejo_id>', methods=['GET', 'POST'])
def editar_consejo(consejo_id):
    if 'user_id' not in session or session.get('rol') != 'admin':
        flash('No tienes permisos para realizar esta acción', 'error')
        return redirect(url_for('inicio'))
   
    conexion = obtener_conexion()
    if conexion is None:
        flash('Error de conexión a la base de datos', 'error')
        return redirect(url_for('admin_consejos'))
       
    cursor = conexion.cursor(dictionary=True)
   
    if request.method == 'POST':
        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        icono = request.form['icono']
        etiquetas = request.form.get('etiquetas', '')
        activo = request.form.get('activo', 0)
       
        try:
            cursor.execute('''
                UPDATE consejos_clima
                SET titulo = %s, descripcion = %s, icono = %s, etiquetas = %s, activo = %s
                WHERE id = %s
            ''', (titulo, descripcion, icono, etiquetas, activo, consejo_id))
           
            conexion.commit()
            flash('Consejo actualizado correctamente', 'success')
           
        except Exception as e:
            flash('Error al actualizar el consejo', 'error')
       
        cursor.close()
        conexion.close()
        return redirect(url_for('admin_consejos'))
   
    cursor.execute('SELECT * FROM consejos_clima WHERE id = %s', (consejo_id,))
    consejo = cursor.fetchone()
    cursor.close()
    conexion.close()
   
    if not consejo:
        flash('Consejo no encontrado', 'error')
        return redirect(url_for('admin_consejos'))
   
    return render_template('editar_consejo.html',
                         consejo=consejo,
                         username=session['username'])

@app.route('/admin/consejos/eliminar/<int:consejo_id>')
def eliminar_consejo(consejo_id):
    if 'user_id' not in session or session.get('rol') != 'admin':
        flash('No tienes permisos para realizar esta acción', 'error')
        return redirect(url_for('inicio'))
   
    conexion = obtener_conexion()
    if conexion is None:
        flash('Error de conexión a la base de datos', 'error')
        return redirect(url_for('admin_consejos'))
       
    cursor = conexion.cursor()
   
    try:
        cursor.execute('DELETE FROM consejos_clima WHERE id = %s', (consejo_id,))
        conexion.commit()
        flash('Consejo eliminado correctamente', 'success')
    except Exception as e:
        flash('Error al eliminar el consejo', 'error')
   
    cursor.close()
    conexion.close()
    return redirect(url_for('admin_consejos'))

# Ruta para obtener consejos (API)
@app.route('/api/consejos')
def get_consejos():
    conexion = obtener_conexion()
    if conexion is None:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
    cursor = conexion.cursor(dictionary=True)
    cursor.execute('SELECT * FROM consejos_clima WHERE activo = TRUE ORDER BY fecha_creacion DESC')
    consejos = cursor.fetchall()
    cursor.close()
    conexion.close()
    return jsonify(consejos)

@app.route('/admin/frases')
def admin_frases():
    if 'user_id' not in session or session.get('rol') != 'admin':
        flash('No tienes permisos para acceder a esta sección', 'error')
        return redirect(url_for('inicio'))
   
    conexion = obtener_conexion()
    if conexion is None:
        flash('Error de conexión a la base de datos', 'error')
        return redirect(url_for('inicio'))
       
    cursor = conexion.cursor(dictionary=True)
    
    # Obtener todas las frases
    cursor.execute('SELECT * FROM frases_dia ORDER BY fecha_publicacion DESC')
    frases = cursor.fetchall()
    cursor.close()
    conexion.close()
   
    return render_template('admin_frases.html',
                         frases=frases,
                         username=session['username'])

@app.route('/admin/frases/agregar', methods=['GET', 'POST'])
def agregar_frase():
    if 'user_id' not in session or session.get('rol') != 'admin':
        flash('No tienes permisos para realizar esta acción', 'error')
        return redirect(url_for('inicio'))
   
    if request.method == 'POST':
        frase = request.form['frase']
        autor = request.form.get('autor', '')
       
        conexion = obtener_conexion()
        if conexion is None:
            flash('Error de conexión a la base de datos', 'error')
            return redirect(url_for('admin_frases'))
           
        cursor = conexion.cursor()
       
        try:
            # Desactivar frases anteriores
            cursor.execute('UPDATE frases_dia SET activa = FALSE')
            
            # Insertar nueva frase activa
            cursor.execute('''
                INSERT INTO frases_dia (frase, autor, activa)
                VALUES (%s, %s, TRUE)
            ''', (frase, autor))
           
            conexion.commit()
            flash('Frase del día agregada correctamente', 'success')
           
        except Exception as e:
            flash('Error al agregar la frase', 'error')
       
        cursor.close()
        conexion.close()
        return redirect(url_for('admin_frases'))
   
    return render_template('agregar_frase.html', username=session['username'])

@app.route('/admin/frases/eliminar/<int:frase_id>')
def eliminar_frase(frase_id):
    if 'user_id' not in session or session.get('rol') != 'admin':
        flash('No tienes permisos para realizar esta acción', 'error')
        return redirect(url_for('inicio'))
   
    conexion = obtener_conexion()
    if conexion is None:
        flash('Error de conexión a la base de datos', 'error')
        return redirect(url_for('admin_frases'))
       
    cursor = conexion.cursor()
   
    try:
        cursor.execute('DELETE FROM frases_dia WHERE id = %s', (frase_id,))
        conexion.commit()
        flash('Frase eliminada correctamente', 'success')
    except Exception as e:
        flash('Error al eliminar la frase', 'error')
   
    cursor.close()
    conexion.close()
    return redirect(url_for('admin_frases'))

# Ruta para obtener la frase activa del día (API)
@app.route('/api/frase_dia')
def get_frase_dia():
    conexion = obtener_conexion()
    if conexion is None:
        return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
    cursor = conexion.cursor(dictionary=True)
    
    # Obtener la frase activa más reciente
    cursor.execute('''
        SELECT * FROM frases_dia 
        WHERE activa = TRUE 
        ORDER BY fecha_publicacion DESC 
        LIMIT 1
    ''')
    frase = cursor.fetchone()
    cursor.close()
    conexion.close()
    
    return jsonify(frase if frase else {})


def limpiar_frases_antiguas():
    """Desactiva frases con más de 12 horas"""
    conexion = obtener_conexion()
    if conexion is None:
        return
        
    cursor = conexion.cursor()
    
    try:
        cursor.execute('''
            UPDATE frases_dia 
            SET activa = FALSE 
            WHERE fecha_publicacion < NOW() - INTERVAL '12 hours'
            AND activa = TRUE
        ''')
        conexion.commit()
    except Exception as e:
        print(f"Error limpiando frases antiguas: {e}")
    finally:
        cursor.close()
        conexion.close()

def programar_limpieza():
    """Programa la limpieza cada hora"""
    schedule.every().hour.do(limpiar_frases_antiguas)
    
    while True:
        schedule.run_pending()
        time.sleep(3600)  # Esperar 1 hora

# Iniciar hilo de limpieza al arrancar la aplicación
if __name__ == '__main__':
    # Ejecutar inicialización del sistema
    inicializar_sistema()
    
    # Iniciar hilo para limpieza automática
    limpieza_thread = Thread(target=programar_limpieza, daemon=True)
    limpieza_thread.start()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)