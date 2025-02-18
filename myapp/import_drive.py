from io import BytesIO
import os
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

SERVICE_ACCOUNT_PATH = os.getenv('SERVICE_ACCOUNT_JSON')
ID_FOLDER = os.getenv('ID_FOLDER_DRIVE')
USER_EMAIL = os.getenv('USER_EMAIL_SERVICE')

def subir_a_drive(file_obj, parent_id=None):
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_PATH,
        scopes=SCOPES
    )
    service = build('drive', 'v3', credentials=creds)

    filename = file_obj.filename

    media = MediaIoBaseUpload(
        file_obj.stream,
        mimetype=file_obj.mimetype,
        resumable=True
    )
    if parent_id:
        file_metadata = {
            'name': filename,
            'parents': [parent_id]
        }
    else:
        file_metadata = {
            'name': filename
        } 

    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    file_id = uploaded_file.get('id')
    print(f"Archivo subido con ID: {file_id}")

    file_id = uploaded_file.get('id')
    print(f"Archivo '{filename}' subido con ID: {file_id} - Carpeta drive_id={parent_id or 'raíz'}")

    return file_id

def descargar_desde_drive(drive_id, filename, mimetype=None, cred_path=SERVICE_ACCOUNT_PATH):
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    creds = service_account.Credentials.from_service_account_file(
        cred_path,
        scopes=SCOPES
    )
    service = build('drive', 'v3', credentials=creds)

    request = service.files().get_media(fileId=drive_id)
    file_handle = BytesIO()
    downloader = MediaIoBaseDownload(file_handle, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()

    file_handle.seek(0)  
    return file_handle    

def crear_carpeta_drive(folder_name):
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_PATH,
        scopes=SCOPES
    )
    service = build('drive', 'v3', credentials=creds)

    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [ID_FOLDER]
    }
    folder = service.files().create(
        body=folder_metadata,
        fields='id'
    ).execute()
    return folder.get('id')

def compartir_carpeta_con_usuario(folder_drive_id, user_email):
    SCOPES = ['https://www.googleapis.com/auth/drive']
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_PATH, 
        scopes=SCOPES
    )
    service = build('drive', 'v3', credentials=creds)

    permission_body = {
        'role': 'writer',      # o 'reader'
        'type': 'user',
        'emailAddress': user_email
    }
    service.permissions().create(
        fileId=folder_drive_id,
        body=permission_body,
        fields='id'
    ).execute()

