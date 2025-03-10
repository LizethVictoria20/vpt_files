import os
from io import BytesIO
import dropbox
from zipfile import ZipFile
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask_principal import Permission, RoleNeed
from flask import Blueprint, abort, flash, render_template, request, redirect, send_file, session, url_for
from myapp.dropbox_utils import (
    crear_carpeta_dropbox,
    subir_a_dropbox,
    descargar_desde_dropbox,
    compartir_carpeta_dropbox,
    USER_EMAIL
)
from myapp.models import DriveFile, DriveFolder, User, Roles, UserRole
from forms import DeleteForm, LoginForm, ImportForm, NewFolderForm, NewUser, ProfileForm, CreateUserForm, GeneralForm

main_bp = Blueprint('main', __name__)
login_manager = LoginManager()
login_manager.init_app(main_bp)
admin_permission = Permission(RoleNeed('admin'))
user_permission = Permission(RoleNeed('user'))


@main_bp.route('/', methods=['GET', 'POST'])
def login():
    from app import bcrypt
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            is_admin = any(role.slug == 'admin' for role in user.roles)
            if is_admin:
                return redirect(url_for('main.listar_carpetas'))
            folder = DriveFolder.query.filter_by(user_id=user.id).first()
            if folder:
                return redirect(url_for('main.ver_carpeta', folder_id=folder.id))
            else:
                # Manejo: si no tiene carpeta, redirigir a otra parte o crearla
                flash("No tienes carpeta asociada. Contacta al administrador.", "warning")
                return redirect(url_for('main.dashboard'))
        else:
            flash('Nombre de usuario o contraseña incorrectos', 'danger')
            return redirect(url_for('main.login'))

    return render_template('login.html', form=form)

@admin_permission.require(http_exception=403)
@user_permission.require(http_exception=403)
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
    return render_template('profile.html', form=form, user=current_user, all_users=all_users)

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('_flashes', None)
    return redirect(url_for('main.login'))

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

# Funcion donde se crean los usuarios clientes
@main_bp.route('/crear-cliente', methods=['GET', 'POST'])
def crear_cliente():
    print("DEBUG: Entrando en crear cliente")
    from app import db
    form = CreateUserForm()
    if request.method == 'POST':
        username = request.form.get('username')
        name = request.form.get('name')
        lastname = request.form.get('lastname')
        email = request.form.get('email')
        password = request.form.get('password')
        usuario_existente = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        if usuario_existente:
            flash("El usuario o el correo ya existen. Prueba con otros.", "error")
            return redirect(url_for('main.crear_cliente'))

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
            flash(f"Error creando usuario: {e}", "error")
            return redirect(url_for('main.crear_cliente'))

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
            flash(f"Error asignando rol: {e}", "error")
            return redirect(url_for('main.crear_cliente'))

        folder_name = f"{name} {lastname}" if lastname else name
        print("DEBUG: Folder name")

        try:
            print("DEBUG: Creando carpeta en Dropbox con nombre =", folder_name)
            dropbox_folder_path = crear_carpeta_dropbox(folder_name)
        except Exception as e:
            print("Error creando carpeta en Drive: {e}")
            return redirect(url_for('main.crear_cliente'))

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
            flash(f"Error creando carpeta en la BD: {e}", "error")
            return redirect(url_for('main.crear_cliente'))

        flash("Usuario creado exitosamente. Carpeta en Drive generada.", "success")
        return redirect(url_for('main.login'))

    return render_template('crear_cliente.html', form=form)

@main_bp.route('/carpeta/<int:folder_id>/upload', methods=['POST'])
@login_required
def subir_archivo(folder_id):
    from app import db
    folder = DriveFolder.query.get_or_404(folder_id)

    if folder.user_id != current_user.id:
        abort(403)

    if request.method == 'POST':
        file_obj = request.files.get('file')
        
        if not file_obj or file_obj.filename == '':
            flash("No seleccionaste ningún archivo", "error")
            return redirect(request.url)

        dropbox_file_path = subir_a_dropbox(file_obj, folder.drive_id)
        
        new_file = DriveFile(
            drive_id=dropbox_file_path,
            filename=file_obj.filename,
            folder_id=folder.id
        )
        db.session.add(new_file)
        db.session.commit()

        flash("Archivo subido exitosamente", "success")
        return redirect(url_for('main.ver_carpeta', folder_id=folder.id))


@main_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    from app import db
    user_to_delete = User.query.get_or_404(user_id)
    db.session.delete(user_to_delete)
    db.session.commit()
    
    flash(f"Usuario '{user_to_delete.username}' eliminado", "success")
    return redirect(url_for('main.profile'))


@admin_permission.require(http_exception=403)
@user_permission.require(http_exception=403)      
@main_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    return render_template('dashboard.html')

@admin_permission.require(http_exception=403)
@user_permission.require(http_exception=403)
@main_bp.route('/import', methods=['GET'])
@login_required
def mostrar_import_form():
    form = ImportForm()
    return render_template("import.html", form=form,)

@admin_permission.require(http_exception=403)
@user_permission.require(http_exception=403)
@main_bp.route('/crear_carpeta', methods=['GET', 'POST'])
@login_required
def crear_carpeta():
    from app import db
    form = NewFolderForm()
    if form.validate_on_submit():
        folder_name = form.name.data
        folder_description = form.description.data

        drive_id = crear_carpeta_dropbox(folder_name)


        nueva_carpeta = DriveFolder(
            drive_id=drive_id,
            name=folder_name,
            description=folder_description
        )
        db.session.add(nueva_carpeta)
        db.session.commit()
        user_email = USER_EMAIL
        compartir_carpeta_dropbox(drive_id, user_email)
        
        flash(f"Carpeta '{folder_name}' creada y compartida con {user_email} exitosamente.", "success")
        return redirect(url_for('main.ver_carpeta', folder_id=nueva_carpeta.id))

    return render_template('crear_carpeta.html', form=form)

@admin_permission.require(http_exception=403)
@user_permission.require(http_exception=403)
@main_bp.route('/carpetas', methods=['GET', 'POST'])
@login_required
def listar_carpetas():
    carpetas = DriveFolder.query.order_by(DriveFolder.created_at.desc()).all()
    delete_form = DeleteForm()
    return render_template('listar_carpetas.html', carpetas=carpetas, delete_form=delete_form)

@main_bp.route('/carpeta/<int:folder_id>')
@login_required
def ver_carpeta(folder_id):
    from flask import abort
    form = GeneralForm()
    folder = DriveFolder.query.get_or_404(folder_id)
    
    # Verifica que el folder pertenezca al usuario logueado
    if folder.user_id != current_user.id:
        abort(403)  # Prohibido si no es su carpeta

    # Renderiza una plantilla que muestre info de la carpeta y un link para subir
    return render_template('ver_carpeta.html', folder=folder, form=form)

@admin_permission.require(http_exception=403)
@user_permission.require(http_exception=403)
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
@user_permission.require(http_exception=403)
@main_bp.route('/eliminar_file/<int:file_id>', methods=['POST'])
@login_required
def eliminar_archivo(file_id):
    from app import db
    archivo = DriveFile.query.get_or_404(file_id)

    db.session.delete(archivo)
    db.session.commit()

    flash(f"Archivo '{archivo.filename}' eliminado de la base de datos", "success")
    return redirect(url_for('main.listar_carpetas'))

@admin_permission.require(http_exception=403)
@user_permission.require(http_exception=403)
@main_bp.route('/eliminar_folder/<int:folder_id>', methods=['POST'])
@login_required
def eliminar_carpeta(folder_id):
    from app import db
    carpeta = DriveFolder.query.get_or_404(folder_id)
    db.session.delete(carpeta)
    db.session.commit()
    flash(f"Carpeta '{carpeta.name}' eliminada exitosamente.", "success")
    return redirect(url_for('main.listar_carpetas'))

# @admin_permission.require(http_exception=403)
# @main_bp.route('/archivos', methods=['GET'])
# @login_required
# def listar_archivos():
#     archivos = DriveFile.query.order_by(DriveFile.uploaded_at.desc()).all()
#     delete_form = DeleteForm()

#     return render_template('archivos_list.html', archivos=archivos, delete_form=delete_form)

@admin_permission.require(http_exception=403)
@user_permission.require(http_exception=403)
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