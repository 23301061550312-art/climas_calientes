import mysql.connector
from werkzeug.security import generate_password_hash

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'formulario_bd'
}

def obtener_conexion():
    return mysql.connector.connect(**DB_CONFIG)

def crear_usuarios():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    
    # Limpiar tabla primero
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
    
    for username, email, password, rol in usuarios:
        # Generar hash REAL de la contraseña
        password_hash = generate_password_hash(password)
        
        # Insertar usuario
        cursor.execute(
            'INSERT INTO usuarios (username, email, password, rol) VALUES (%s, %s, %s, %s)',
            (username, email, password_hash, rol)
        )
        
        print(f"✅ Usuario creado: {username} | Contraseña: {password} | Rol: {rol}")
    
    conexion.commit()
    cursor.close()
    conexion.close()
    
    print("\n" + "="*50)
    print("🎯 USUARIOS CREADOS EXITOSAMENTE")
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

if __name__ == '__main__':
    crear_usuarios()