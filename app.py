# app.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from myapp.routes import main_bp
from myapp.admin_routes import admin_bp
from myapp.superadmin_routes import superadmin_bp
import openai
from myapp.models import db, User
from flask_wtf import CSRFProtect


openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai

app = Flask(__name__)
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'main.login'
login_manager = LoginManager(app)

app.config["SECRET_KEY"] = "dev-secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mydb.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

migrate = Migrate(app, db)
app.register_blueprint(main_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(superadmin_bp)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


if __name__ == "__main__":
    app.run(debug=True)
