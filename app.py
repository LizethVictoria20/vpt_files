# app.py
import os
from flask import Flask
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_wtf import CSRFProtect
import openai

# Importa db solo una vez
from myapp.db import db

# Importa tus modelos y rutas (asegúrate de que no importen otra instancia de db)
from myapp.routes import main_bp
from myapp.admin_routes import admin_bp
from myapp.superadmin_routes import superadmin_bp
from myapp.models import User, DriveFolder, DriveFile, Roles, UserRole

openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai

app = Flask(__name__)
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'main.login'

# Configuración de la base de datos (solo una vez)
if os.environ.get('DATABASE_URL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydb.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret')

# Inicializar db solo una vez
db.init_app(app)

# Configurar migración
migrate = Migrate(app, db)

# Registrar blueprints
app.register_blueprint(main_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(superadmin_bp)

# Crear tablas
with app.app_context():
    db.create_all()
    roles_to_create = [
        {'name': 'Administrador', 'slug': 'admin'},
        {'name': 'Usuario', 'slug': 'user'},
        {'name': 'Superadmin', 'slug': 'superadmin'},
        {'name': 'Lector', 'slug': 'lector'}
    ]
    for role_data in roles_to_create:
        existing_role = Roles.query.filter_by(slug=role_data['slug']).first()
        if not existing_role:
            new_role = Roles(
                name=role_data['name'], 
                slug=role_data['slug']
            )
            db.session.add(new_role)
    
    db.session.commit()
    
    # Crear usuarios iniciales
    from myapp.init_users import create_initial_users
    create_initial_users()
    

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

if __name__ == "__main__":
    app.run(debug=True)