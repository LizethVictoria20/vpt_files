from flask_wtf import FlaskForm
from wtforms import FileField, StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ImportForm(FlaskForm):
    archivos = FileField('Archivo', validators=[DataRequired()])
    descripcion = StringField('Descripción')
    etiquetas = StringField('Etiquetas')
    
    
class DeleteForm(FlaskForm):
    pass

class NewUser(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    lastname = StringField('Lastname', validators=[DataRequired()])
    telephone = StringField('Telephone', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Crear usuario')
    
class NewFolderForm(FlaskForm):
    name = StringField('Nombre de la carpeta', validators=[DataRequired()])
    description = TextAreaField('Descripción (opcional)')