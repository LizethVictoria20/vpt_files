import os
from flask_login import login_required, login_user, logout_user, current_user
from flask_principal import Permission, RoleNeed
from flask import Blueprint, flash, render_template, request, redirect, session, url_for
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


@main_bp.route('/import', methods=['GET'])
@login_required
def mostrar_import_form():
    form = ImportForm()
    return render_template("import.html", form=form,)


@main_bp.route('/import', methods=['POST'])
@login_required
def procesar_import_form():
    from myapp.import_drive import subir_a_drive
    from app import db
    print("¡Entrando a procesar_import_form!")
    form = ImportForm()
    if form.validate_on_submit():

        file = request.files.get('archivo')
        if not file:
            flash("No se ha seleccionado ningún archivo", "error")
            return redirect(url_for('main.mostrar_import_form'))

        descripcion = request.form.get('descripcion')
        etiquetas = request.form.get('etiquetas')

        ALLOWED_EXTENSIONS = {'csv', 'xls', 'xlsx', 'json', 'xml'}
        filename = file.filename
        if not filename:
            flash("El archivo no tiene nombre.", "error")
            return redirect(url_for('main.mostrar_import_form'))

        ext = filename.rsplit('.', 1)[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            flash("Tipo de archivo no soportado", "error")
            return redirect(url_for('main.mostrar_import_form'))

        drive_id = subir_a_drive(file)
        new_file = DriveFile(
            drive_id=drive_id,
            filename=file.filename,
            mimetype=file.mimetype,
            description=descripcion,
            etiquetas=etiquetas
        )
        db.session.add(new_file)
        db.session.commit()

        print(f"Archivo {filename} importado con éxito. ID de Drive: {drive_id}")

        flash(f"Archivo {filename} importado con éxito.", "success")

    return redirect(url_for('main.listar_archivos'))

@admin_permission.require(http_exception=403)
@main_bp.route('/archivos', methods=['GET'])
@login_required
def listar_archivos():
    from myapp.models import DriveFile
    archivos = DriveFile.query.order_by(DriveFile.uploaded_at.desc()).all()
    return render_template('archivos_list.html', archivos=archivos)