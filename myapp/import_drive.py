from io import BytesIO
import os
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

SERVICE_ACCOUNT_PATH = os.getenv('SERVICE_ACCOUNT_JSON')
ID_FOLDER = os.getenv('ID_FOLDER_DRIVE')

def subir_a_drive(file_obj):
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
    
    file_metadata = {
        'name': filename,
        'parents': [ID_FOLDER]
    }

    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    file_id = uploaded_file.get('id')
    print(f"Archivo subido con ID: {file_id}")

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