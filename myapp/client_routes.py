from collections import defaultdict
import os
import uuid
from flask import Blueprint, Response, abort, flash, jsonify, render_template, request, redirect, send_file, send_from_directory, session, url_for
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask_principal import Permission, RoleNeed
from httplib2 import Credentials

from forms import GeneralForm
from myapp.models import DriveFile, DriveFolder


client_bp = Blueprint('cliente', __name__, url_prefix='/cliente')
login_manager = LoginManager()
login_manager.init_app(client_bp)
superadmin_permission = Permission(RoleNeed('superadmin'))
admin_permission = Permission(RoleNeed('admin'))
lector_permission = Permission(RoleNeed('lector'))
client_permission = Permission(RoleNeed('cliente'))

