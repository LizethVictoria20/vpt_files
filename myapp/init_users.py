import os
from dotenv import load_dotenv
from myapp.db import db
from myapp.models import User, Roles, UserRole

def load_initial_users_from_env():
    """
    Cargar usuarios desde variables de entorno
    """
    load_dotenv()  # Cargar variables de entorno
    
    initial_users = []
    
    # Buscar usuarios basado en un patrón de variables de entorno
    for i in range(1, 5):  # Asumiendo 4 usuarios
        prefix = f'INIT_USER_{i}_'
        
        # Verificar si existe al menos el nombre de usuario
        username = os.getenv(f'{prefix}USERNAME')
        if not username:
            continue
        
        user_data = {
            'username': username,
            'name': os.getenv(f'{prefix}NAME', ''),
            'lastname': os.getenv(f'{prefix}LASTNAME', ''),
            'telephone': os.getenv(f'{prefix}TELEPHONE', ''),
            'email': os.getenv(f'{prefix}EMAIL', ''),
            'password': os.getenv(f'{prefix}PASSWORD', ''),
            'role_slug': os.getenv(f'{prefix}ROLE', 'user')
        }
        
        initial_users.append(user_data)
    
    return initial_users

def create_initial_users():
    """
    Crear usuarios iniciales desde variables de entorno
    """
    # Cargar usuarios desde env
    initial_users = load_initial_users_from_env()
    
    # Verificar si hay usuarios para crear
    if not initial_users:
        print("No se encontraron usuarios para inicializar")
        return

    # Asegurarse de que los roles existan
    roles = {
        role.slug: role for role in Roles.query.all()
    }

    # Crear usuarios
    for user_data in initial_users:
        # Verificar si el usuario ya existe
        existing_user = User.query.filter(
            (User.username == user_data['username']) | 
            (User.email == user_data['email'])
        ).first()

        if not existing_user:
            # Crear nuevo usuario
            new_user = User(
                username=user_data['username'],
                name=user_data['name'],
                telephone=user_data['telephone'],
                lastname=user_data['lastname'],
                email=user_data['email']
            )
            new_user.set_password(user_data['password'])
            
            # Agregar usuario a la sesión
            db.session.add(new_user)
            db.session.flush()  # Obtener ID de usuario

            # Asignar rol
            role = roles.get(user_data['role_slug'])
            if role:
                user_role = UserRole(
                    user_id=new_user.id, 
                    role_id=role.id
                )
                db.session.add(user_role)

    # Confirmar cambios
    db.session.commit()
    print("Usuarios iniciales creados exitosamente")

# Comando de Flask (opcional)
def init_users_command():
    """
    Comando de Flask para inicializar usuarios
    Uso: flask init-users
    """
    create_initial_users()