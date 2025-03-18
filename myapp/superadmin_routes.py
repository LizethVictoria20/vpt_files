from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
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
    
    # Ya no necesitamos verificación manual aquí porque está en el decorador
    users = User.query.all()
    roles = Roles.query.all()
    
    if request.method == 'POST':
        user_id = request.form['user_id']
        new_role_ids = [int(role_id) for role_id in request.form.getlist('roles')]
        
        user = User.query.get(user_id)
        user.roles = [role for role in roles if role.id in new_role_ids]
        db.session.commit()
        
        flash('Permisos actualizados correctamente', 'success')
        return redirect(url_for('superadmin.gestionar_permisos'))
    
    return render_template('gestionar_permisos.html', users=users, roles=roles)