from myapp.models import DriveFile, DriveFolder, User


def buscar_contenido(q, current_user, is_admin=False):
  """
  Lógica de búsqueda:
  - Archivos (DriveFile) según 'q' (coincidencia en filename)
  - Si no es admin, filtra que DriveFolder.user_id == current_user.id
  - Si es admin y se desea, también buscar usuarios (por nombre, correo)
  
  Retorna un dict con:
    {
      "files": [...],
      "users": [...]
    }
  """
  q = (q or "").strip()
  data = {
      "files": [],
      "users": []
  }

  # 1) Buscar archivos
  files_query = DriveFile.query.join(DriveFolder)
  if not is_admin:
      # Solo ver archivos de mi propiedad
      files_query = files_query.filter(DriveFolder.user_id == current_user.id)
  # Filtrar por coincidencia en filename
  if q:
      files_query = files_query.filter(DriveFile.filename.ilike(f"%{q}%"))

  files = files_query.all()
  for f in files:
      data["files"].append({
          "id": f.id,
          "filename": f.filename,
          "drive_id": f.drive_id,
          "etiquetas": f.etiquetas,
          "group_label": f.group_label,
          "folder_id": f.folder_id,
      })

  # 2) (Opcional) Si es admin, también buscar usuarios
  if is_admin:
      # Buscar por nombre, apellido, email, etc.
      # Ajusta la lógica a lo que necesites (por ej. username, name, lastname)
      users_query = User.query
      if q:
          users_query = users_query.filter(
              (User.email.ilike(f"%{q}%")) |
              (User.name.ilike(f"%{q}%")) |
              (User.lastname.ilike(f"%{q}%")) |
              (User.username.ilike(f"%{q}%"))
          )

      found_users = users_query.all()
      for u in found_users:
          data["users"].append({
              "id": u.id,
              "username": u.username,
              "email": u.email,
              "name": u.name,
              "lastname": u.lastname,
          })

  return data