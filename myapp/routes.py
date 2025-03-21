from collections import defaultdict
from operator import or_
import os
from io import BytesIO
import dropbox
from zipfile import ZipFile
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask_principal import Permission, RoleNeed
from flask import Blueprint, Response, abort, flash, jsonify, render_template, request, redirect, send_file, session, url_for
from myapp.dropbox_utils import (
    _get_dbx,
    crear_carpeta_dropbox,
    generar_enlace_dropbox_temporal,
    subir_a_dropbox,
    descargar_desde_dropbox,
    compartir_carpeta_dropbox,
    eliminar_de_dropbox,
    USER_EMAIL
)
from myapp.models import DriveFile, DriveFolder, User, Roles, UserRole
from forms import DeleteForm, LoginForm, ImportForm, NewFolderForm, NewUser, ProfileForm, CreateUserForm, GeneralForm
from myapp.services.preview_files_service import preview_file_logic
from myapp.services.search_service import buscar_archivos

main_bp = Blueprint('main', __name__)
login_manager = LoginManager()
login_manager.init_app(main_bp)
superadmin_permission = Permission(RoleNeed('superadmin'))
admin_permission = Permission(RoleNeed('admin'))
lector_permission = Permission(RoleNeed('lector'))
client_permission = Permission(RoleNeed('cliente'))



@main_bp.route('/', methods=['GET', 'POST'])
def login():
    from app import bcrypt
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter(or_(User.username == username, User.email == username)).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            
            is_superadmin = any(role.slug == 'superadmin' for role in user.roles)
            is_admin = any(role.slug == 'admin' for role in user.roles)
            is_cliente = any(role.slug == 'cliente' for role in user.roles)
            
            folder = DriveFolder.query.filter_by(user_id=user.id).first()
            
            if is_superadmin:
                return redirect(url_for('superadmin.gestionar_permisos'))
            elif is_admin:
                return redirect(url_for('main.listar_carpetas'))
            elif is_cliente and folder:
                return redirect(url_for('main.import_files', folder_id=folder.id))
            elif folder:
                return redirect(url_for('main.ver_carpeta', folder_id=folder.id))
            else:
                flash("No tienes carpeta asociada. Contacta al administrador.", "warning")
                return redirect(url_for('main.listar_carpetas'))
        else:
            flash('Nombre de usuario o contraseña incorrectos', 'danger')
            return redirect(url_for('main.login'))

    return render_template('login.html', form=form)

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    from myapp.models import User
    from app import db
    user = User.query.get(current_user.id)
    all_users = User.query.all()
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.name = form.nombre.data
        current_user.lastname = form.apellido.data
        current_user.email = form.email.data
        current_user.telephone = form.telefono.data
        db.session.commit()
        flash('Perfil actualizado con éxito', 'success')
        return redirect(url_for('main.profile'))
    return render_template('profile-cliente.html', form=form, user=current_user, all_users=all_users)

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('_flashes', None)
    return redirect(url_for('main.login'))


@superadmin_permission.require(http_exception=403)      
# Esta funcion puede crear usuarios con roles
@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    from app import db
    new_user = NewUser()
    if request.method == 'POST':
        username = request.form.get('username')
        name = request.form.get('name')
        lastname = request.form.get('lastname')
        telephone = request.form.get('telephone')
        email = request.form.get('email')
        password = request.form.get('password')
        role_input = request.form.get('role')

        if not (username and name and lastname and telephone and email and password):
            flash("Todos los campos son obligatorios", "warning")
            return redirect(url_for('main.register'))

        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash("Este usuario o email ya está en uso", "danger")
            return redirect(url_for('main.register'))
        new_user = User(
            username=username,
            name=name,
            lastname=lastname,
            telephone=telephone,
            email=email
        )
        new_user.set_password(password)
        role_obj = Roles.query.filter_by(slug=role_input).first()
        if not role_obj:
            flash("No se encontró el rol solicitado", "danger")
            return redirect(url_for('main.register'))
        new_user.roles.append(role_obj)
      
        db.session.add(new_user)
        db.session.commit()
        flash("Usuario registrado exitosamente", "success")
        return redirect(url_for('main.carpetas'))

    return render_template('register.html', new_user=new_user)

@superadmin_permission.require(http_exception=403)
@main_bp.route('/crear-cliente', methods=['GET', 'POST'])
def crear_cliente():
    print("DEBUG: Entrando en crear cliente")
    from app import db
    form = CreateUserForm()
    errors = {}
    
    if request.method == 'POST':
        username = request.form.get('username')
        name = request.form.get('name')
        lastname = request.form.get('lastname')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            errors['confirm_password'] = "Las contraseñas no coinciden."
        
        usuario_username_existente = User.query.filter(User.username == username).first()
        usuario_email_existente = User.query.filter(User.email == email).first()
        
        if usuario_username_existente:
            errors['username'] = "Este nombre de usuario ya está en uso."
        if usuario_email_existente:
            errors['email'] = "Este correo electrónico ya está registrado."
        
        if not errors:
            nuevo_usuario = User(
                username=username,
                name=name,
                lastname=lastname,
                email=email
            )
            nuevo_usuario.set_password(password)
            db.session.add(nuevo_usuario)
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"DEBUG: Error creando usuario: {str(e)}")
                errors['general'] = f"Error al crear usuario: {e}"
                return render_template('crear_cliente.html', form=form, errors=errors, 
                                       username=username, name=name, lastname=lastname, email=email)

            rol_cliente = Roles.query.filter_by(slug='cliente').first()
            if not rol_cliente:
                rol_cliente = Roles(name='Cliente', slug='cliente')
                db.session.add(rol_cliente)
                db.session.commit()
            nuevo_usuario.roles.append(rol_cliente)
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"DEBUG: Error asignando rol: {str(e)}")
                errors['general'] = f"Error al asignar rol: {e}"
                return render_template('crear_cliente.html', form=form, errors=errors, 
                                      username=username, name=name, lastname=lastname, email=email)

            folder_name = f"{name} {lastname}" if lastname else name
            print("DEBUG: Folder name")

            try:
                print("DEBUG: Creando carpeta en Dropbox con nombre =", folder_name)
                dropbox_folder_path = crear_carpeta_dropbox(folder_name)
            except Exception as e:
                print(f"DEBUG: Error creando carpeta en Drive: {str(e)}")
                errors['general'] = f"Error al crear carpeta en Drive: {e}"
                return render_template('crear_cliente.html', form=form, errors=errors, 
                                      username=username, name=name, lastname=lastname, email=email)

            print("DEBUG: Registrando carpeta en la tabla DriveFolder...")
            nueva_carpeta_db = DriveFolder(
                user_id=nuevo_usuario.id,
                drive_id=dropbox_folder_path,
                name=folder_name,
                description="Carpeta del cliente"
            )
            print("DEBUG: Se creo la nueva carpeta")
            db.session.add(nueva_carpeta_db)
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"DEBUG: Error creando carpeta en la BD: {str(e)}")
                errors['general'] = f"Error al registrar carpeta: {e}"
                return render_template('crear_cliente.html', form=form, errors=errors, 
                                      username=username, name=name, lastname=lastname, email=email)

            return redirect(url_for('main.login'))
        else:
            return render_template('crear_cliente.html', form=form, errors=errors, 
                                  username=username, name=name, lastname=lastname, email=email)

    return render_template('crear_cliente.html', form=form, errors=errors)

@main_bp.route('/carpeta/<int:folder_id>/import', methods=['GET'])
@login_required
def import_files(folder_id):
    form = GeneralForm()
    
    folder = DriveFolder.query.get_or_404(folder_id)
    
    if folder.user_id != current_user.id:
        abort(403)

    return render_template("import_files.html", form=form, folder=folder)


@client_permission.require(http_exception=403)      
@superadmin_permission.require(http_exception=403)      
@main_bp.route('/carpeta/<int:folder_id>/upload', methods=['POST'])
@login_required
def subir_archivo(folder_id):
    from app import db
    folder = DriveFolder.query.get_or_404(folder_id)
    if folder.user_id != current_user.id:
        abort(403)

    files_list = request.files.getlist('file') 

    file_label = request.form.get('fileLabel')
    group_label = request.form.get('groupLabel')

    if not files_list or len(files_list) == 0:
        return redirect(request.url)

    if not file_label or not group_label:
        return redirect(request.url)

    subfolder_path = f"{folder.drive_id}/{group_label}/{file_label}"
    try:
        crear_carpeta_dropbox(subfolder_path)
    except dropbox.exceptions.ApiError as e:
        # si la subcarpeta ya existe, ignorar
        if "WriteConflictError('folder'" in str(e):
            print("Subcarpeta ya existía, continuamos.")
        else:
            return redirect(url_for('main.ver_carpeta', folder_id=folder.id))

    archivos_subidos = 0
    for f_obj in files_list:
        if not f_obj or f_obj.filename == '':
            continue 

        try:
            final_path_in_dropbox = subir_a_dropbox(f_obj, subfolder_path)
        except Exception as e:
            flash(f"Error subiendo {f_obj.filename}: {e}", "error")
            continue

        new_file = DriveFile(
            drive_id=final_path_in_dropbox,
            filename=f_obj.filename,
            folder_id=folder.id,
            etiquetas=file_label,
            group_label=group_label
        )
        db.session.add(new_file)
        archivos_subidos += 1

    db.session.commit()

    if archivos_subidos > 0:
        flash(f"Se subieron {archivos_subidos} archivo(s) exitosamente", "success")
    else:
        flash("No se pudo subir ningún archivo (todos eran vacíos o fallaron).", "warning")
    
    return redirect(url_for('main.ver_carpeta', folder_id=folder.id))


@superadmin_permission.require(http_exception=403)      
@main_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    from app import db
    user_to_delete = User.query.get_or_404(user_id)
    db.session.delete(user_to_delete)
    db.session.commit()
    
    flash(f"Usuario '{user_to_delete.username}' eliminado", "success")
    return redirect(url_for('main.profile'))


@client_permission.require(http_exception=403)
@superadmin_permission.require(http_exception=403)      
@main_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    return render_template('dashboard.html')

@admin_permission.require(http_exception=403)
@superadmin_permission.require(http_exception=403)
@admin_permission.require(http_exception=403)
@main_bp.route('/import', methods=['GET'])
@login_required
def mostrar_import_form():
    form = ImportForm()
    return render_template("import.html", form=form,) 

@client_permission.require(http_exception=403)
@superadmin_permission.require(http_exception=403)   
@main_bp.route('/carpeta/<int:folder_id>')
@login_required
def ver_carpeta(folder_id):
    from flask import abort
    form = GeneralForm()
    folder = DriveFolder.query.get_or_404(folder_id)
    user_is_cliente = any(r.slug == "cliente" for r in current_user.roles)

    if folder.user_id != current_user.id:
        abort(403)

    archivos = DriveFile.query.filter_by(folder_id=folder.id).all()
    by_group = defaultdict(lambda: defaultdict(list))
    for f in archivos:
        g = f.group_label or "Sin categoría" 
        lbl = f.etiquetas or "Sin etiqueta" 
        by_group[g][lbl].append(f)

    return render_template('ver_carpeta_as_cliente.html', folder=folder, form=form, by_group=by_group, user_is_cliente=user_is_cliente)

@admin_permission.require(http_exception=403)
@superadmin_permission.require(http_exception=403)
@main_bp.route('/descargar/<int:file_id>', methods=['GET'])
@login_required
def descargar_archivo(file_id):
    archivo = DriveFile.query.get_or_404(file_id)

    fh = descargar_desde_dropbox(archivo.drive_id)

    return send_file(
        fh,
        as_attachment=True,
        download_name=archivo.filename,
        mimetype=archivo.mimetype or 'application/octet-stream'
    )

@admin_permission.require(http_exception=403)
@client_permission.require(http_exception=403)
@superadmin_permission.require(http_exception=403)
@main_bp.route('/eliminar_file/<int:file_id>', methods=['POST', 'GET'])
@login_required
def eliminar_archivo(file_id):
    from app import db
    archivo = DriveFile.query.get_or_404(file_id)

    if archivo.folder.user_id != current_user.id:
        abort(403)

    try:
        dbx = _get_dbx()
        dbx.files_delete_v2(archivo.drive_id)

        db.session.delete(archivo)
        db.session.commit()

        flash("Archivo eliminado correctamente", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar archivo: {e}", "error")

    return redirect(url_for('main.ver_carpeta', folder_id=archivo.folder.id))


@admin_permission.require(http_exception=403)
@superadmin_permission.require(http_exception=403)
@main_bp.route('/eliminar_folder/<int:folder_id>', methods=['POST'])
@login_required
def eliminar_carpeta(folder_id):
    from app import db
    carpeta = DriveFolder.query.get_or_404(folder_id)
    db.session.delete(carpeta)
    db.session.commit()
    flash(f"Carpeta '{carpeta.name}' eliminada exitosamente.", "success")
    return redirect(url_for('main.listar_carpetas'))

@admin_permission.require(http_exception=403)
@superadmin_permission.require(http_exception=403)
@lector_permission.require(http_exception=403)
@main_bp.route('/carpetas', methods=['GET', 'POST'])
@login_required
def listar_carpetas():
    usuarios = User.query.all()
    delete_form = DeleteForm()
    return render_template('listar_carpetas.html', usuarios=usuarios, delete_form=delete_form)


@admin_permission.require(http_exception=403)
@superadmin_permission.require(http_exception=403)
@main_bp.route('/descargar_carpeta/<int:folder_id>', methods=['GET'])
@login_required
def descargar_carpeta(folder_id):
    from app import db
    from myapp.models import DriveFolder, DriveFile
    
    carpeta = DriveFolder.query.get_or_404(folder_id)
    archivos = DriveFile.query.filter_by(folder_id=carpeta.id).all()
    
    if not archivos:
        flash(f"La carpeta '{carpeta.name}' no tiene archivos o no existe.", "warning")
        return redirect(url_for('main.listar_carpetas'))
    
    memory_file = BytesIO()
    with ZipFile(memory_file, 'w') as zipf:
        for archivo in archivos:
            fh = descargar_desde_dropbox(
                drive_id=archivo.drive_id,
                filename=archivo.filename,
                mimetype=archivo.mimetype,
            )
            
            file_data = fh.read()
            zipf.writestr(archivo.filename, file_data)
    memory_file.seek(0)

    return send_file(
        memory_file, 
        as_attachment=True,
        download_name=f"{carpeta.name}.zip",
        mimetype="application/zip"
    )
    
@main_bp.route("/buscar_archivos_json")
@login_required
def buscar_archivos_json():
    q = request.args.get("q", "").strip()
    files = buscar_archivos(q, current_user, is_admin=False)
    return jsonify(files)

@main_bp.route("/preview_file/<int:file_id>")
def preview_file(file_id):
    return preview_file_logic(file_id)


