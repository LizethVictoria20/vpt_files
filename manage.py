# manage.py
import click
from flask.cli import FlaskGroup
from myapp import create_app, db
from myapp.models import User, Informe, Roles

def create_my_app():
    return create_app()

cli = FlaskGroup(create_app=create_my_app)

@cli.command('create_admin')
def create_admin():
    # ejemplo de crear un usuario admin
    admin = User(username='admin', password_hash='hashedpwd')
    db.session.add(admin)
    db.session.commit()
    print("Admin creado.")

if __name__ == '__main__':
    cli()
