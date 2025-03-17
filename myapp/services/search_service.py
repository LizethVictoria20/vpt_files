from myapp.models import DriveFile, DriveFolder, User

def buscar_archivos(q, current_user, is_admin=False):
    q = (q or "").strip()

    files_query = DriveFile.query.join(DriveFolder)

    if not is_admin:
        files_query = files_query.filter(DriveFolder.user_id == current_user.id)

    if q:
        files_query = files_query.filter(DriveFile.filename.ilike(f"%{q}%"))

    found_files = files_query.all()

    results = []
    for f in found_files:
        results.append({
            "id": f.id,
            "filename": f.filename,
            "drive_id": f.drive_id,
            "etiquetas": f.etiquetas,
            "group_label": f.group_label,
            "folder_id": f.folder_id,
        })

    return results


def buscar_usuarios(q):
    q = (q or "").strip()

    users_query = User.query

    if q:
        users_query = users_query.filter(
            (User.email.ilike(f"%{q}%")) |
            (User.name.ilike(f"%{q}%")) |
            (User.lastname.ilike(f"%{q}%")) |
            (User.username.ilike(f"%{q}%"))
        )

    found_users = users_query.all()

    results = []
    for u in found_users:
        role_names = [role.name for role in u.roles]
        folders_count = len(u.folders)
        results.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "name": u.name,
            "lastname": u.lastname,
            "roles": role_names,
            "folders_count": folders_count,
        })

    return results
