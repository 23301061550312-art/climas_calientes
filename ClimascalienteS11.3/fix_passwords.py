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

def actualizar_contraseñas():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    
    # Lista de usuarios a actualizar
    usuarios = [
        {'username': 'admin', 'password': '123456'},
        {'username': 'superadmin', 'password': '123456'},
        {'username': 'demo', 'password': '123456'},
        {'username': 'usuario1', 'password': '123456'}
    ]
    
    for usuario in usuarios:
        # Generar hash correcto de la contraseña
        password_hash = generate_password_hash(usuario['password'])
        
        # Actualizar en la base de datos
        cursor.execute('UPDATE usuarios SET password = %s WHERE username = %s', 
                      (password_hash, usuario['username']))
        
        print(f"✓ Contraseña actualizada para: {usuario['username']} -> {usuario['password']}")
    
    conexion.commit()
    cursor.close()
    conexion.close()
    print("\n¡Todas las contraseñas han sido actualizadas!")
    print("Ahora puedes iniciar sesión con:")
    print("Usuario: admin | Contraseña: 123456")
    print("Usuario: superadmin | Contraseña: 123456")

if __name__ == '__main__':
    actualizar_contraseñas()