import os        # Import modul untuk operasi file dan direktori
from datetime import datetime    # Import modul untuk mendapatkan tanggal dan waktu saat ini
from google.oauth2 import service_account    # Import modul untuk otentikasi menggunakan akun layanan Google
from googleapiclient.discovery import build    # Import modul untuk membangun service API Google Drive
from googleapiclient.http import MediaFileUpload    # Import modul untuk mengunggah file ke Google Drive

# Fungsi untuk mengunggah file ke Google Drive
def upload_to_drive(file_path, folder_id):
    # Load credentials dari file credential.json (file JSON akun layanan Google)
    creds = service_account.Credentials.from_service_account_file('credential.json')

    # Buat objek service untuk API Google Drive versi 3
    service = build('drive', 'v3', credentials=creds)

    # Metadata file yang akan diunggah (nama dan folder tujuan)
    file_metadata = {
        'name': os.path.basename(file_path),    # Nama file diambil dari path-nya
        'parents': [folder_id]  # ID folder tujuan di Google Drive
    }
    media = MediaFileUpload(file_path, resumable=True)    # Buat objek media dari file yang akan diunggah (dengan opsi resumable)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()    # Kirim request untuk mengunggah file ke Google Drive

    print(f"File {file_path} berhasil diunggah ke Google Drive dengan ID: {file.get('id')}")    # Tampilkan ID file yang berhasil diunggah

# Buat timestamp dalam format dd-mm-YYYY
timestamp = datetime.now().strftime("%d-%m-%Y")

# Daftar nama file yang akan diunggah, ditambahkan tanggal pada nama file
files_to_upload = [
    f"data_bukit_vista_{timestamp}.xlsx",
    f"property_description_{timestamp}.xlsx"
]

# ID folder tujuan di Google Drive
FOLDER_ID = '1zdLvHzqvv0PGJ6Bt5zhL52yxMTi845ou'

# Looping untuk mengunggah semua file dalam daftar
for file in files_to_upload:
    if os.path.exists(file):    # Cek apakah file tersedia di direktori lokal
        upload_to_drive(file, FOLDER_ID)    # Panggil fungsi upload jika file ada
    else:
        print(f"File {file} tidak ditemukan.")    # Tampilkan pesan jika file tidak ditemukan
