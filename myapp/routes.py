from flask_principal import Permission, RoleNeed
from flask import Blueprint, flash, render_template, request, redirect, session, url_for

main_bp = Blueprint('main', __name__)
admin_permission = Permission(RoleNeed('admin'))
user_permission = Permission(RoleNeed('user'))


@main_bp.route('/', methods=['GET', 'POST'])
def login():          
  return render_template('login.html')
