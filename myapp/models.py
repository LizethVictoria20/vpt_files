from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

user_folders = db.Table('user_folders',
  db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
  db.Column('folder_id', db.Integer, db.ForeignKey('drive_folders.id'), primary_key=True)
)

class Roles(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    users = db.relationship("User", secondary="user_roles", back_populates="roles")

class UserRole(db.Model):
  __tablename__ = 'user_roles'
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
  role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), primary_key=True)

class User(db.Model, UserMixin):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(64), nullable=False)
  name = db.Column(db.String(64), nullable=True)
  lastname = db.Column(db.String(64), nullable=True)
  telephone = db.Column(db.String(64), nullable=True)
  email = db.Column(db.String(64), nullable=False)
  password_hash = db.Column(db.String(128), nullable=False)
  created_at = db.Column(db.DateTime, default=datetime.utcnow)
  roles = db.relationship("Roles", secondary="user_roles", back_populates="users")
  folders = db.relationship("DriveFolder", backref="user", lazy=True)

  __table_args__ = (
    db.UniqueConstraint('username', name='uq_user_username'),
    db.UniqueConstraint('email', name='uq_user_email'),
  )
  def set_password(self, password):
    from app import bcrypt
    self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

  def check_password(self, password):
    from app import bcrypt
    return bcrypt.check_password_hash(self.password_hash, password)

class DriveFolder(db.Model):
    __tablename__ = 'drive_folders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), name='fk_drivefolders_user_id')
    drive_id = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    files = db.relationship('DriveFile', backref='folder', lazy=True)

    def __repr__(self):
        return f"<DriveFolder name={self.name}, drive_id={self.drive_id}>"


class DriveFile(db.Model):
  __tablename__ = 'drive_files'

  id = db.Column(db.Integer, primary_key=True)
  drive_id = db.Column(db.String(100), nullable=False)
  filename = db.Column(db.String(255), nullable=False)
  mimetype = db.Column(db.String(100), nullable=True)
  description = db.Column(db.Text, nullable=True)
  etiquetas = db.Column(db.String(255), nullable=True)
  uploaded_at = db.Column(db.DateTime, server_default=db.func.now())
  folder_id = db.Column(db.Integer, db.ForeignKey('drive_folders.id'))

  def __repr__(self):
    return f"<DriveFile filename={self.filename} drive_id={self.drive_id}>"