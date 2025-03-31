import json
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from forms import GeneralForm
from myapp.models import User, Roles

superadmin_bp = Blueprint('superadmin', __name__, url_prefix='/superadmin')

def superadmin_required(f):
    """ Decorador para asegurar que el usuario actual es superadmin """
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))  # O la ruta de login que uses
        # Verifica que el usuario tenga el rol superadmin
        if not any(role.slug == 'superadmin' for role in current_user.roles):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@superadmin_bp.route('/gestionar_permisos', methods=['GET', 'POST'])
@login_required
@superadmin_required
def gestionar_permisos():
    from app import db
    form = GeneralForm()
    users = User.query.all()
    roles_path = os.path.join(os.path.dirname(__file__), 'services', 'roles.json')
    with open(roles_path, 'r', encoding='utf-8') as f:
        roles_data = json.load(f)
    
    # Extraer la lista de roles
    roles = roles_data.get('roles', [])
    if request.method == 'POST':
        user_id = request.form['user_id']
        new_role_id = request.form.get('selected_role')
        
        if not new_role_id:
            flash('Por favor, selecciona un rol para asignar', 'error')
            return redirect(url_for('superadmin.gestionar_permisos'))
        
        user = User.query.get(user_id)
        if not user:
            flash('Usuario no encontrado', 'error')
            return redirect(url_for('superadmin.gestionar_permisos'))
        
        new_role = Roles.query.get(new_role_id)
        if not new_role:
            flash('Rol no encontrado', 'error')
            return redirect(url_for('superadmin.gestionar_permisos'))
        
        user.roles = [new_role]
        
        try:
            db.session.commit()
            flash(f'El rol {new_role.name} ha sido asignado al usuario {user.username}', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar los permisos: {str(e)}', 'error')
        
        return redirect(url_for('superadmin.gestionar_permisos'))
    
    return render_template('gestionar_permisos.html', users=users, roles=roles, form=form)