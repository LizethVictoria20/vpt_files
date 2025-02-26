import os
from io import BytesIO
from zipfile import ZipFile
from flask_login import login_required, login_user, logout_user, current_user
from flask_principal import Permission, RoleNeed
from flask import Blueprint, flash, render_template, request, redirect, send_file, session, url_for
from myapp.import_drive import SERVICE_ACCOUNT_PATH, USER_EMAIL, compartir_carpeta_con_usuario, crear_carpeta_drive, subir_a_drive, descargar_desde_drive
from myapp.models import DriveFile, DriveFolder, User, Roles, UserRole
from forms import DeleteForm, LoginForm, ImportForm, NewFolderForm, NewUser, ProfileForm

main_bp = Blueprint('main', __name__)
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
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('main.listar_carpetas'))
        else:
            flash('Nombre de usuario o contraseña incorrectos', 'danger')
            return redirect(url_for('main.login'))

    return render_template('login.html', form=form)

@admin_permission.require(http_exception=403)
@user_permission.require(http_exception=403)
@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    from app import db
    from myapp.models import User
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

@admin_permission.require(http_exception=403)
@main_bp.route('/register', methods=['GET', 'POST'])
@login_required
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
        return redirect(url_for('main.profile'))

    return render_template('register.html', new_user=new_user)

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

        drive_id = crear_carpeta_drive(folder_name)


        nueva_carpeta = DriveFolder(
            drive_id=drive_id,
            name=folder_name,
            description=folder_description
        )
        db.session.add(nueva_carpeta)
        db.session.commit()
        user_email = USER_EMAIL
        compartir_carpeta_con_usuario(drive_id, user_email)
        
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

@admin_permission.require(http_exception=403)
@user_permission.require(http_exception=403)
@main_bp.route('/carpeta/<int:folder_id>', methods=['GET', 'POST'])
@login_required
def ver_carpeta(folder_id):
    from myapp.models import db
    delete_form = DeleteForm()
    carpeta = DriveFolder.query.get_or_404(folder_id)

    form = ImportForm()
    
    if form.validate_on_submit():
        files = request.files.getlist('archivos')
        if not files or files[0].filename == '':
            flash("No se han seleccionado archivos", "error")
            return redirect(url_for('main.ver_carpeta', folder_id=folder_id))

        descripcion = request.form.get('descripcion')
        etiquetas = request.form.get('etiquetas')

        for file in files:
            if file.filename:
                drive_id = subir_a_drive(file, carpeta.drive_id)

                new_file = DriveFile(
                    drive_id=drive_id,
                    filename=file.filename,
                    mimetype=file.mimetype,
                    folder_id=carpeta.id,
                    description=descripcion,
                    etiquetas=etiquetas
                )
                db.session.add(new_file)
        db.session.commit()
        flash(f"Se han subido {len(files)} archivo(s) a la carpeta {carpeta.name}.", "success")
        return redirect(url_for('main.ver_carpeta', folder_id=folder_id))

    archivos = DriveFile.query.filter_by(folder_id=folder_id).all()
    return render_template('ver_carpeta.html', 
                           carpeta=carpeta, 
                           archivos=archivos, 
                           form=form, 
                           delete_form=delete_form)

# @main_bp.route('/import', methods=['POST'])
# @login_required
# def procesar_import_form():
#     from app import db
#     print("¡Entrando a procesar_import_form!")
#     form = ImportForm()
#     if form.validate_on_submit():
#         files = request.files.getlist('archivos')
#         if not files or len(files) == 0 or files[0].filename == '':
#             flash("No se han seleccionado archivos", "error")
#             return redirect(url_for('main.mostrar_import_form'))

#         descripcion = request.form.get('descripcion')
#         etiquetas = request.form.get('etiquetas')

#         ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx', 'json', 'xml'}

#         for file in files:
#             filename = file.filename
#             if not filename:
#                 flash("Uno de los archivos no tiene nombre.", "error")
#                 continue

#             ext = filename.rsplit('.', 1)[-1].lower()
#             if ext not in ALLOWED_EXTENSIONS:
#                 flash(f"Archivo {filename} - Tipo de archivo no soportado", "error")
#                 continue

#             drive_id = subir_a_drive(file)

#             new_file = DriveFile(
#                 drive_id=drive_id,
#                 filename=filename,
#                 mimetype=file.mimetype,
#                 description=descripcion,
#                 etiquetas=etiquetas
#             )
#             db.session.add(new_file)

#         db.session.commit() 
#         flash(f"Se han importado {len(files)} archivos.", "success")
#     return redirect(url_for('main.listar_archivos'))

@admin_permission.require(http_exception=403)
@user_permission.require(http_exception=403)
@main_bp.route('/descargar/<int:file_id>', methods=['GET'])
@login_required
def descargar_archivo(file_id):
    archivo = DriveFile.query.get_or_404(file_id)

    fh = descargar_desde_drive(
        drive_id=archivo.drive_id,
        filename=archivo.filename,
        mimetype=archivo.mimetype,
        cred_path=SERVICE_ACCOUNT_PATH
    )

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
            fh = descargar_desde_drive(
                drive_id=archivo.drive_id,
                filename=archivo.filename,
                mimetype=archivo.mimetype,
                cred_path=SERVICE_ACCOUNT_PATH
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