from collections import defaultdict
from flask import Blueprint, Response, abort, flash, jsonify, render_template, request, redirect, send_file, session, url_for
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask_principal import Permission, RoleNeed
from myapp.dropbox_utils import _get_dbx
from myapp.models import DriveFile, DriveFolder, User
from forms import DeleteForm
from myapp.services.preview_files_service import preview_file_logic
from myapp.services.search_service import buscar_archivos, buscar_usuarios


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
            return redirect(url_for('auth.login'))  # O la ruta de login que uses
        # Por ejemplo, si tus roles tienen un 'slug' o 'name' = 'admin'
        if not any(role.slug == 'admin' for role in current_user.roles):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin_permission.require(http_exception=403)
@superadmin_permission.require(http_exception=403)
@lector_permission.require(http_exception=403)
@admin_bp.route('/carpetas', methods=['GET', 'POST'])
@login_required
def listar_carpetas():
    usuarios = User.query.all()
    delete_form = DeleteForm()
    return render_template('listar_carpetas.html', usuarios=usuarios, delete_form=delete_form)


@admin_bp.route('/admin_carpeta/<int:folder_id>')
@login_required
@admin_required  # tu decorador para validar rol admin
def admin_ver_carpeta(folder_id):
    folder = DriveFolder.query.get_or_404(folder_id)
    archivos = DriveFile.query.filter_by(folder_id=folder.id).all()

    by_group = defaultdict(lambda: defaultdict(list))
    for f in archivos:
        g = f.group_label or "Sin categoría"
        lbl = f.etiquetas or "Sin etiqueta"
        by_group[g][lbl].append(f)

    return render_template(
        'admin_ver_usuario.html',
        folder=folder,
        by_group=by_group
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