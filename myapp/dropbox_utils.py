# dropbox_utils.py

import os
import time
import uuid
import dropbox
from dropbox.files import WriteMode, FolderMetadata, FileMetadata
from dropbox.oauth import DropboxOAuth2Flow

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
USER_EMAIL = os.getenv('USER_EMAIL_SERVICE')
DROPBOX_APP_KEY = os.getenv('DROPBOX_APP_KEY')
DROPBOX_APP_SECRET = os.getenv('DROPBOX_APP_SECRET')
DROPBOX_REFRESH_TOKEN = os.getenv('DROPBOX_REFRESH_TOKEN')


def _get_dbx():
    dbx = dropbox.Dropbox(
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET,
    )
    return dbx

def crear_carpeta_dropbox(folder_path: str) -> str:
    dbx = _get_dbx()
    try:
        if not folder_path.startswith('/'):
            folder_path = '/' + folder_path

        res = dbx.files_create_folder_v2(folder_path)
        return folder_path
    except dropbox.exceptions.ApiError as e:
        raise e

def subir_a_dropbox(file_obj, dropbox_folder_path: str) -> str:
    dbx = _get_dbx()
    if not dropbox_folder_path.startswith('/'):
        dropbox_folder_path = '/' + dropbox_folder_path

    original_name = file_obj.filename
    name, ext = os.path.splitext(original_name)
    unique_name = f"{name}_{uuid.uuid4().hex}{ext}"

    final_path = f"{dropbox_folder_path}/{unique_name}"

    # Leer bytes
    file_bytes = file_obj.read()
    file_obj.seek(0)

    try:
        res = dbx.files_upload(file_bytes, final_path, mode=WriteMode('add'))
        print(f"[dropbox_utils] Subido: {res.name} en {res.path_lower}")

        return res.path_lower

    except dropbox.exceptions.ApiError as e:
        print(f"[dropbox_utils] Error subiendo archivo: {e}")
        raise e

def descargar_desde_dropbox(dropbox_file_path: str) -> bytes:
    dbx = _get_dbx()
    if not dropbox_file_path.startswith('/'):
        dropbox_file_path = '/' + dropbox_file_path

    try:
        metadata, res = dbx.files_download(dropbox_file_path)
        print(f"[dropbox_utils] Descargado archivo {metadata.name} con id {metadata.id}")
        return res.content  
    except dropbox.exceptions.ApiError as e:
        print(f"[dropbox_utils] Error descargando archivo: {e}")
        raise e

def compartir_carpeta_dropbox(folder_path: str) -> str:
    dbx = _get_dbx()
    if not folder_path.startswith('/'):
        folder_path = '/' + folder_path

    try:
        res = dbx.sharing_create_shared_link_with_settings(folder_path)
        print(f"[dropbox_utils] Carpeta compartida en link: {res.url}")
        return res.url
    except dropbox.exceptions.ApiError as e:
        if e.error.is_shared_link_already_exists():
            links = dbx.sharing_list_shared_links(path=folder_path).links
            if links:
                print(f"[dropbox_utils] Link existente: {links[0].url}")
                return links[0].url
        print(f"[dropbox_utils] Error compartiendo carpeta: {e}")
        raise e
