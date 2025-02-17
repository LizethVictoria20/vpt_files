from flask_wtf import FlaskForm
from wtforms import FileField, StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ImportForm(FlaskForm):
    archivo = FileField('Archivo', validators=[DataRequired()])
    descripcion = StringField('Descripción')
    etiquetas = StringField('Etiquetas')