import os
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Fungsi untuk mengunggah file ke Google Drive
def upload_to_drive(file_path, folder_id):
    # Load credentials dari file credential.json
    creds = service_account.Credentials.from_service_account_file('credential.json')

    # Buat service Google Drive
    service = build('drive', 'v3', credentials=creds)

    # Upload file
    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [folder_id]  # ID folder tujuan di Google Drive
    }
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    print(f"File {file_path} berhasil diunggah ke Google Drive dengan ID: {file.get('id')}")

# Generate timestamp
timestamp = datetime.now().strftime("%d-%m-%Y")

# File yang akan diunggah dengan nama berformat tanggal
files_to_upload = [
    f"data_bukit_vista_{timestamp}.xlsx",
    f"property_description_{timestamp}.xlsx"
]

# ID folder tujuan di Google Drive
FOLDER_ID = '1zdLvHzqvv0PGJ6Bt5zhL52yxMTi845ou'  # Ganti dengan ID folder Google Drive Anda

# Unggah semua file
for file in files_to_upload:
    if os.path.exists(file):
        upload_to_drive(file, FOLDER_ID)
    else:
        print(f"File {file} tidak ditemukan.")