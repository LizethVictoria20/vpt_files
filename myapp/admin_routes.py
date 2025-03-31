from collections import defaultdict
from flask import Blueprint, Response, abort, flash, jsonify, render_template, request, redirect, send_file, session, url_for
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask_principal import Permission, RoleNeed
from myapp.dashboard import calculate_percent_change, get_charts_data, get_file_types_stats
from myapp.dropbox_utils import _get_dbx
from myapp.models import DriveFile, DriveFolder, Roles, User, UserRole
from forms import DeleteForm
from myapp.services.preview_files_service import preview_file_logic
from myapp.services.search_service import buscar_archivos, buscar_usuarios
from datetime import datetime, timedelta
from sqlalchemy import func
import calendar

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
login_manager = LoginManager()
login_manager.init_app(admin_bp)
superadmin_permission = Permission(RoleNeed('superadmin'))
admin_permission = Permission(RoleNeed('admin'))
lector_permission = Permission(RoleNeed('lector'))
client_permission = Permission(RoleNeed('cliente'))


def admin_required(f):
    """ Decorador para asegurar que el usuario actual es admin """
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not any(role.slug == 'admin' or role.slug == 'lector' or role.slug == 'superadmin'  for role in current_user.roles):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@lector_permission.require(http_exception=403)      
@admin_bp.route('/admin_carpeta/<int:folder_id>')
@login_required
@admin_required 
def admin_ver_carpeta(folder_id):
    folder = DriveFolder.query.get_or_404(folder_id)
    archivos = DriveFile.query.filter_by(folder_id=folder.id).all()
    is_lector = any(role.slug == 'lector' for role in current_user.roles)

    by_group = defaultdict(lambda: defaultdict(list))
    for f in archivos:
        g = f.group_label or "Sin categoría"
        lbl = f.etiquetas or "Sin etiqueta"
        by_group[g][lbl].append(f)

    return render_template(
        'admin_ver_usuario.html',
        folder=folder,
        by_group=by_group,
        is_lector=is_lector
    )


@admin_bp.route("/preview_file/<int:file_id>")
def admin_preview_file(file_id):
    return preview_file_logic(file_id)


@admin_bp.route("/buscar_usuarios_json", methods=["GET"])
def buscar():
    q = request.args.get("q", "")
    files = buscar_archivos(q, current_user, is_admin=True)
    users = buscar_usuarios(q)
    return jsonify({
        "files": files,
        "users": users
    })
    

@admin_bp.route("/buscar_archivos_en_carpeta/<int:folder_id>", methods=["GET"])
@login_required
@admin_required
def buscar_archivos_en_carpeta(folder_id):
    q = request.args.get("q", "").strip()
    folder = DriveFolder.query.get_or_404(folder_id)
    files_query = DriveFile.query.filter_by(folder_id=folder.id)

    if q:
        files_query = files_query.filter(DriveFile.filename.ilike(f"%{q}%"))
    archivos = files_query.all()

    results = []
    for f in archivos:
        results.append({
            "id": f.id,
            "filename": f.filename,
            "folder_id": f.folder_id,
            "group_label": f.group_label,
            "etiquetas": f.etiquetas
        })

    return jsonify({"files": results})


@admin_permission.require(http_exception=403)
@admin_bp.route('/eliminar_file/<int:file_id>', methods=['POST'])
@login_required
def eliminar_archivo(file_id):
    from app import db
    archivo = DriveFile.query.get_or_404(file_id)

    try:
        dbx = _get_dbx()
        dbx.files_delete_v2(archivo.drive_id)
        folder_id = archivo.folder.id 
        db.session.delete(archivo)
        db.session.commit()

        return jsonify({"success": True, "message": "Archivo eliminado correctamente", "folder_id": folder_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Error al eliminar archivo: {str(e)}"}), 500
    
    
@superadmin_permission.require(http_exception=403)      
@admin_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    from app import db
    # Fechas para filtrar
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    start_of_week = today - timedelta(days=today.weekday())
    last_week_start = start_of_week - timedelta(days=7)
    last_week_end = start_of_week - timedelta(days=1)
    
    # Primer día del mes actual
    first_day_of_month = today.replace(day=1)
    
    # Último día del mes anterior
    last_month = (first_day_of_month - timedelta(days=1))
    first_day_last_month = last_month.replace(day=1)
    
    # Archivos subidos hoy
    files_today_count = DriveFile.query.filter(
        func.date(DriveFile.uploaded_at) == today
    ).count()
    
    # Archivos subidos ayer
    files_yesterday_count = DriveFile.query.filter(
        func.date(DriveFile.uploaded_at) == yesterday
    ).count()
    
    # Archivos subidos esta semana
    files_this_week_count = DriveFile.query.filter(
        func.date(DriveFile.uploaded_at) >= start_of_week,
        func.date(DriveFile.uploaded_at) <= today
    ).count()
    
    # Archivos subidos la semana pasada
    files_last_week_count = DriveFile.query.filter(
        func.date(DriveFile.uploaded_at) >= last_week_start,
        func.date(DriveFile.uploaded_at) <= last_week_end
    ).count()
    
    # Archivos subidos este mes
    files_this_month_count = DriveFile.query.filter(
        func.date(DriveFile.uploaded_at) >= first_day_of_month,
        func.date(DriveFile.uploaded_at) <= today
    ).count()
    
    # Archivos subidos el mes pasado
    files_last_month_count = DriveFile.query.filter(
        func.date(DriveFile.uploaded_at) >= first_day_last_month,
        func.date(DriveFile.uploaded_at) < first_day_of_month
    ).count()
    
    # Usuarios nuevos este mes
    new_users_this_month = User.query.filter(
        func.date(User.created_at) >= first_day_of_month,
        func.date(User.created_at) <= today
    ).count()
    
    # Usuarios nuevos el mes pasado
    new_users_last_month = User.query.filter(
        func.date(User.created_at) >= first_day_last_month,
        func.date(User.created_at) < first_day_of_month
    ).count()
    
    # Calcular porcentajes de cambio
    files_today_percent = calculate_percent_change(files_today_count, files_yesterday_count)
    files_week_percent = calculate_percent_change(files_this_week_count, files_last_week_count)
    files_month_percent = calculate_percent_change(files_this_month_count, files_last_month_count)
    new_users_percent = calculate_percent_change(new_users_this_month, new_users_last_month)
    
    # Crear diccionario de estadísticas
    stats = {
        'files_today': files_today_count,
        'files_today_percent': files_today_percent,
        'files_week': files_this_week_count,
        'files_week_percent': files_week_percent,
        'files_month': files_this_month_count,
        'files_month_percent': files_month_percent,
        'new_users_month': new_users_this_month,
        'new_users_percent': new_users_percent
    }
    
    # Obtener archivos recientes para la tabla
    recent_files = DriveFile.query.order_by(DriveFile.uploaded_at.desc()).limit(10).all()
    recent_files = db.session.query(DriveFile, User)\
    .join(DriveFolder, DriveFile.folder_id == DriveFolder.id)\
    .join(User, DriveFolder.user_id == User.id)\
    .order_by(DriveFile.uploaded_at.desc())\
    .limit(5).all()

    # Datos para las gráficas
    charts_data = get_charts_data()
    file_types = get_file_types_stats()

    return render_template(
        'dashboard.html', 
        stats=stats,
        recent_files=recent_files,
        file_types=file_types,
        charts_data=charts_data
    )

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    from app import db
    user_to_delete = User.query.get_or_404(user_id)
    
    if user_to_delete.id == current_user.id:
        flash('No puedes eliminar tu propio usuario', 'error')
        return redirect(url_for('main.listar_carpetas'))
    
    try:
        user_folders = DriveFolder.query.filter_by(user_id=user_id).all()
        folder_count = len(user_folders)
        
        file_count = 0
        for folder in user_folders:
            files = DriveFile.query.filter_by(folder_id=folder.id).all()
            file_count += len(files)
            for file in files:
                db.session.delete(file)
            db.session.delete(folder)
        
        UserRole.query.filter_by(user_id=user_id).delete()
        db.session.delete(user_to_delete)
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
    
    return redirect(url_for('main.listar_carpetas'))
