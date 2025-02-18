import os
from flask_login import login_required, login_user, logout_user, current_user
from flask_principal import Permission, RoleNeed
from flask import Blueprint, flash, render_template, request, redirect, send_file, session, url_for
from myapp.import_drive import SERVICE_ACCOUNT_PATH, subir_a_drive, descargar_desde_drive
from myapp.models import DriveFile, User
from forms import LoginForm, ImportForm

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
            return redirect(url_for('main.mostrar_import_form'))
        else:
            flash('Nombre de usuario o contraseña incorrectos', 'danger')
            return redirect(url_for('main.login'))

    return render_template('login.html', form=form)


@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('_flashes', None)
    return redirect(url_for('main.login'))


@main_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    return render_template('dashboard.html')


@main_bp.route('/import', methods=['GET'])
@login_required
def mostrar_import_form():
    form = ImportForm()
    return render_template("import.html", form=form,)


@main_bp.route('/import', methods=['POST'])
@login_required
def procesar_import_form():
    from app import db
    print("¡Entrando a procesar_import_form!")
    form = ImportForm()
    if form.validate_on_submit():
        files = request.files.getlist('archivos')
        if not files or len(files) == 0 or files[0].filename == '':
            flash("No se han seleccionado archivos", "error")
            return redirect(url_for('main.mostrar_import_form'))

        descripcion = request.form.get('descripcion')
        etiquetas = request.form.get('etiquetas')

        ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx', 'json', 'xml'}

        for file in files:
            filename = file.filename
            if not filename:
                flash("Uno de los archivos no tiene nombre.", "error")
                continue

            ext = filename.rsplit('.', 1)[-1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                flash(f"Archivo {filename} - Tipo de archivo no soportado", "error")
                continue

            drive_id = subir_a_drive(file)

            new_file = DriveFile(
                drive_id=drive_id,
                filename=filename,
                mimetype=file.mimetype,
                description=descripcion,
                etiquetas=etiquetas
            )
            db.session.add(new_file)

        db.session.commit() 
        flash(f"Se han importado {len(files)} archivos.", "success")
    return redirect(url_for('main.listar_archivos'))

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
@main_bp.route('/archivos', methods=['GET'])
@login_required
def listar_archivos():
    from myapp.models import DriveFile
    archivos = DriveFile.query.order_by(DriveFile.uploaded_at.desc()).all()
    return render_template('archivos_list.html', archivos=archivos)