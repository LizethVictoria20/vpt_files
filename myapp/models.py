from datetime import datetime
import bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin


db = SQLAlchemy()

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
  email = db.Column(db.String(64), nullable=False)
  password_hash = db.Column(db.String(128), nullable=False)
  created_at = db.Column(db.DateTime, default=datetime.utcnow)
  roles = db.relationship("Roles", secondary="user_roles", back_populates="users")
  __table_args__ = (
    db.UniqueConstraint('username', name='uq_user_username'),
    db.UniqueConstraint('email', name='uq_user_email'),
  )
  def set_password(self, password):
    self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

  def check_password(self, password):
    return bcrypt.check_password_hash(self.password_hash, password)


