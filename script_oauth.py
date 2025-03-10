# script_oauth.py
import os
import dropbox
from dropbox.oauth import DropboxOAuth2FlowNoRedirect

DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")     # Debe estar en tu entorno
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")

# Iniciamos el flujo con token_access_type='offline'
flow = DropboxOAuth2FlowNoRedirect(
    consumer_key=DROPBOX_APP_KEY,
    consumer_secret=DROPBOX_APP_SECRET,
    token_access_type='offline',  # Para obtener refresh token
    scope=['files.content.write','files.content.read']  # los scopes que necesites
)

authorize_url = flow.start()
print("1) Ve a esta URL y autoriza la aplicación:")
print(authorize_url)
print("2) Copia el 'authorization code' que aparezca y pégalo aquí.")
code = input("Ingresa el codigo: ").strip()

oauth_result = flow.finish(code)

print("Access Token:", oauth_result.access_token)
print("Refresh Token:", oauth_result.refresh_token)
print("Expires At:", oauth_result.expires_at)
