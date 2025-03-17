# services/preview_service.py
from flask import Response

from myapp.dropbox_utils import descargar_desde_dropbox, generar_enlace_dropbox_temporal
from myapp.models import DriveFile

def preview_file_logic(file_id):
    f = DriveFile.query.get_or_404(file_id)
    extension = f.filename.rsplit('.', 1)[-1].lower()

    contenido = descargar_desde_dropbox(f.drive_id)

    if extension in ["pdf"]:
        return Response(contenido, mimetype="application/pdf")
    elif extension in ["jpg", "jpeg", "png", "gif"]:
        mimetype = f"image/{extension}" if extension != "jpg" else "image/jpeg"
        return Response(contenido, mimetype=mimetype)
    elif extension in ["doc", "docx"]:
        link_temporal = generar_enlace_dropbox_temporal(f.drive_id)
        iframe_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8" />
            <title>Vista previa: {f.filename}</title>
        </head>
        <body style="margin:0; padding:0;">
            <iframe
                src="https://docs.google.com/gview?embedded=true&url={link_temporal}"
                style="width:100%; height:100vh;"
                frameborder="0">
            </iframe>
        </body>
        </html>
        """
        return Response(iframe_html, mimetype="text/html")
    else:
        return Response(contenido, mimetype="application/octet-stream")
