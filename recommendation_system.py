import streamlit as st      # Mengimpor Streamlit untuk membangun UI web
import pandas as pd     # Mengimpor pandas untuk manipulasi data
import numpy as np      # Mengimpor numpy untuk operasi numerik
import json     # Mengimpor json untuk bekerja dengan data JSON
import ast      # Mengimpor ast untuk evaluasi string sebagai literal Python
from sklearn.metrics.pairwise import cosine_similarity      # Mengimpor fungsi cosine_similarity dari sklearn
import io       # Mengimpor io
import os       # Mengimpor os
import re       # Mengimpor re
import datetime # Mengimpor satetime
from googleapiclient.discovery import build    # Import library untuk membangun layanan Google API
from google.oauth2 import service_account    # Import library untuk autentikasi menggunakan service account

# === Streamlit UI ===
st.set_page_config(page_title="🏠 Top Property Recommendations by Bukit Vista", layout="wide")      # Mengatur konfigurasi halaman Streamlit

# Menambahkan CSS untuk menempatkan gambar di tengah dan mengatur jarak
st.markdown(
    """
    <style>
    .centered-content {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: auto;
        margin-top: 10px; /* Menambahkan jarak ke atas */
    }
    .centered-image {
        margin-top: 5px; /* Menambahkan jarak antara gambar dan teks */
    }
    </style>
    """, 
    unsafe_allow_html=True    # Mengizinkan penggunaan HTML dalam markdown
)

# Menampilkan logo dengan jarak yang lebih dekat
st.markdown(
    '<div class="centered-content"><img src="https://www.bukitvista.com/wp-content/uploads/2021/06/BukitVista-LOGO-ONLY-transparent.png" width="150" class="centered-image"></div>',
    unsafe_allow_html=True    # Mengizinkan HTML untuk menampilkan gambar
)

# === Setup Google Drive API Credentials ===
@st.cache_resource        # Cache hasil untuk efisiensi pemanggilan ulang
def get_drive_service():
    try:
        # Ambil kredensial dari Streamlit secrets
        credentials_info = json.loads(st.secrets["gdrive"]["credentials"])    # Mengambil kredensial dari secrets
        creds = service_account.Credentials.from_service_account_info(credentials_info)    # Membuat objek kredensial
        service = build("drive", "v3", credentials=creds)    # Membangun service Google Drive
        return service
    except Exception as e:
        return None    # Jika gagal, kembalikan None

# === Fungsi untuk Mendapatkan File Terbaru di Google Drive ===
@st.cache_data        # Cache hasil agar tidak download ulang tiap reload
def get_latest_file(folder_id):
    drive_service = get_drive_service()    # Ambil service Google Drive
    if drive_service is None:        # Jika gagal, keluar
        return None, None

    results = drive_service.files().list(    # Mengambil file Excel dalam folder berdasarkan ID folder
        q=f"'{folder_id}' in parents and mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'",
        fields="files(id, name, createdTime)",        # Hanya ambil ID, nama, dan tanggal dibuat
        orderBy="createdTime desc"        # Urutkan dari file terbaru
    ).execute()    # Ambil list file dalam folder yang sesuai kriteria

    files = results.get("files", [])    # Ambil list file
    if not files:    # Jika kosong, kembalikan None
        return None, None

    file_pattern = re.compile(r"data_bukit_vista_(\d{2}-\d{2}-\d{4})\.xlsx")    # Pola nama file
    latest_file = None
    latest_date = None

    for file in files:    # Loop tiap file
        match = file_pattern.match(file["name"])    # Cek apakah nama file sesuai pola
        if match:
            file_date = datetime.datetime.strptime(match.group(1), "%d-%m-%Y")    # Parsing tanggal dari nama file
            if latest_date is None or file_date > latest_date:    # Cari tanggal terbaru
                latest_date = file_date
                latest_file = file    # Simpan file terbaru

    if latest_file:    # Jika ditemukan file
        return latest_file["id"], latest_file["name"]    # Kembalikan ID dan nama
    else:
        return None, None

# === Fungsi untuk Mengunduh dan Membaca File Terbaru ===
@st.cache_data    # Cache data yang sudah di-load
def load_latest_data(folder_id):
    file_id, file_name = get_latest_file(folder_id)    # Ambil file terbaru
    if file_id is None:    # Jika tidak ada
        return None, None

    drive_service = get_drive_service()    # Ambil service Drive
    if drive_service is None:
        return None, None

    request = drive_service.files().get_media(fileId=file_id)    # Request untuk download file
    file_content = io.BytesIO(request.execute())    # Simpan hasil download ke memory
    df = pd.read_excel(file_content, dtype={"price_info": str})    # Baca file Excel ke dataframe
    return df, file_name    # Kembalikan dataframe dan nama file

# === Load Data dari Google Drive ===
FOLDER_ID = "1zdLvHzqvv0PGJ6Bt5zhL52yxMTi845ou"    # ID folder Google Drive
result = load_latest_data(FOLDER_ID)    # Load data terbaru dari folder
if result is None:
    raise ValueError("load_latest_data() returned None. Check if the folder contains the necessary files.")    # Validasi jika gagal
df, file_name = result    # Pecah hasil ke dalam dataframe dan nama file

if df is None:    # Jika dataframe kosong, hentikan
    st.stop()

# === Process DataFrame Features ===
feature_columns = [         # Menentukan kolom fitur yang digunakan untuk perhitungan
    'title_vectorizer', 'property_type_vectorizer', 
    'tags_vectorizer', 'area_vectorizer', 'price_info'    # Kolom fitur yang digunakan
]

df[feature_columns] = df[feature_columns].fillna(0)     # Mengisi nilai NaN dengan 0 pada kolom fitur

# Fungsi untuk mengonversi string yang berisi vektor menjadi array numpy
def safe_eval(x):
    if isinstance(x, str):
        try:
            return np.array(ast.literal_eval(x))  # Mencoba evaluasi sebagai list Python
        except (SyntaxError, ValueError):
            try:
                return np.array(json.loads(x))  # Mencoba parsing sebagai JSON
            except (json.JSONDecodeError, TypeError):
                return np.array([0])  # Jika masih gagal, kembalikan array nol
    return np.array(x)    # Jika sudah array, langsung kembalikan

# Mengonversi vektor pada semua kolom fitur kecuali 'price_info'
for col in feature_columns:
    if col != 'price_info':  # Pastikan hanya fitur lain yang diproses, Jangan proses kolom price_info
        df[col] = df[col].apply(safe_eval)    # Ubah semua kolom string vector jadi array

# Menggabungkan semua fitur ke dalam satu array numpy
combined_features = np.array([np.hstack([row[col] for col in feature_columns if col != 'price_info']) for _, row in df.iterrows()])

# Menghitung matriks kesamaan kosinus antar properti
similarity_matrix = cosine_similarity(combined_features)    # Hitung similarity antar properti

# === Property Recommendation Function ===
def recommend_properties(selected_area, selected_property_type, top_n=4):
    # Filter dataset berdasarkan area dan property type
    filtered_df = df[(df["area"] == selected_area) & (df["property_type"] == selected_property_type)]

    if filtered_df.empty:    # Jika hasil kosong
        return "No properties found for this selection"

    # Menggunakan properti pertama sebagai referensi untuk rekomendasi
    reference_index = filtered_df.index[0]    # Ambil properti pertama sebagai acuan
    similar_indices = np.argsort(similarity_matrix[reference_index])[::-1][1:top_n+1]    # Urutkan properti serupa

    return df.iloc[similar_indices][["title", "image_url", "price_info", "area", "property_type"]]    # Kembalikan data rekomendasi

# Header dan deskripsi
st.markdown(
    "<h2 style='text-align: center; color: black; font-size: 40px;'>"
    "Discover the Finest Vacation Rentals in Bali and Yogyakarta</h2>",
    unsafe_allow_html=True
)
st.markdown("<p style='text-align: center;'>We are here to fulfill your desire for great comfort, whether for a short-term or long-term stay in Bali or Yogyakarta.</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>The choice is yours.</p>", unsafe_allow_html=True)
st.markdown("---")      # Menambahkan garis pemisah

# Tambahkan CSS untuk mengatur lebar selectbox, styling untuk dropdown
st.markdown(
    """
    <style>
    div[data-baseweb="select"] {
        width: 600px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# **Dropdown untuk memilih Area dan Property Type**
selected_area = st.selectbox("📍 Select Location:", df["area"].unique())
selected_property_type = st.selectbox("🏠 Select Property Type:", df["property_type"].unique())

# **Button to Get Recommendations**
if st.button("✨ Get Recommendations"):    # Jika tombol ditekan
    recommended = recommend_properties(selected_area, selected_property_type)    # Ambil hasil rekomendasi

    if isinstance(recommended, str):  # Jika properti tidak ditemukan, tampilkan pesan error
        st.error(recommended)
    else:
        st.markdown("<h3 style='text-align: left;'>✔ Exclusive Property Recommendations Just for You</h3>", unsafe_allow_html=True)

        # **Display results in a grid**
        cols = st.columns(2)  # Membagi tampilan ke dalam 2 kolom
        for idx, (_, row) in enumerate(recommended.iterrows()):    # Loop hasil
            with cols[idx % 2]:    # Tampilkan secara bergantian di dua kolom
                st.image(row["image_url"], width=350)    # Gambar properti
                st.subheader(row["title"])    # Judul properti
                st.write(f"🗺️ **Location:** {row['area']}")    # Lokasi
                st.write(f"🏡 **Type:** {row['property_type']}")    # Tipe
                st.write(f"💸 **Price:** {row['price_info']}")    # Harga
