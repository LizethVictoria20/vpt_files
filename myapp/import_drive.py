import os
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseUpload

SERVICE_ACCOUNT_PATH = os.getenv('SERVICE_ACCOUNT_JSON')
ID_FOLDER = os.getenv('ID_FOLDER_DRIVE')

def subir_a_drive(file_obj):
    """
    Sube un archivo a Drive dentro de la carpeta cuyo ID ya existe y está compartida.
    """
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_PATH,
        scopes=SCOPES
    )
    service = build('drive', 'v3', credentials=creds)

    # Nombre que tendrá el archivo en Drive
    filename = file_obj.filename

    # Prepara la subida desde el FileStorage
    media = MediaIoBaseUpload(
        file_obj.stream,
        mimetype=file_obj.mimetype,
        resumable=True
    )
    
    file_metadata = {
        'name': filename,
        'parents': [ID_FOLDER]  # ID de tu carpeta compartida
    }

    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    file_id = uploaded_file.get('id')
    print(f"Archivo subido con ID: {file_id}")

    return file_id