import streamlit as st      # Mengimpor Streamlit untuk membangun UI web
import pandas as pd     # Mengimpor pandas untuk manipulasi data
import numpy as np      # Mengimpor numpy untuk operasi numerik
import json     # Mengimpor json untuk bekerja dengan data JSON
import ast      # Mengimpor ast untuk evaluasi string sebagai literal Python
from sklearn.metrics.pairwise import cosine_similarity      # Mengimpor fungsi cosine_similarity dari sklearn
import io       # Mengimpor io
import os       # Mengimpor os
import re       # Mengimpor re
import base64
import datetime # Mengimpor satetime
from googleapiclient.discovery import build
from google.oauth2 import service_account

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
        margin-top: 20px; /* Menambahkan jarak ke atas */
    }
    .centered-image {
        margin-top: 10px; /* Menambahkan jarak antara gambar dan teks */
    }
    </style>
    """, 
    unsafe_allow_html=True
)

# Menampilkan logo dengan jarak yang lebih dekat
st.markdown(
    '<div class="centered-content"><img src="https://www.bukitvista.com/wp-content/uploads/2021/06/BukitVista-LOGO-ONLY-transparent.png" width="200" class="centered-image"></div>',
    unsafe_allow_html=True
)

# === Autentikasi Google Drive API ===
# === Autentikasi Google Drive API ===
@st.cache_resource
def get_drive_service():
    credential_base64 = os.getenv("CREDENTIAL_JSON")  # Ambil kredensial dalam format Base64

    if credential_base64 is None:
        st.error("❌ Secret 'CREDENTIAL_JSON' tidak ditemukan. Periksa konfigurasi di GitHub Secrets atau Streamlit Secrets.")
        return None

    try:
        credential_json = base64.b64decode(credential_base64).decode("utf-8")
        creds_dict = json.loads(credential_json)
        creds = service_account.Credentials.from_service_account_info(creds_dict)
        service = build("drive", "v3", credentials=creds)
        st.success("✅ Google Drive API berhasil diinisialisasi!")
        return service
    except Exception as e:
        st.error(f"❌ Gagal menginisialisasi Google Drive API: {e}")
        return None

# === Fungsi untuk Mendapatkan File Terbaru di Google Drive ===
@st.cache_data
def get_latest_file(folder_id):
    drive_service = get_drive_service()
    if drive_service is None:
        return None, None

    results = drive_service.files().list(
        q=f"'{folder_id}' in parents and mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'",
        fields="files(id, name, createdTime)",
        orderBy="createdTime desc"
    ).execute()

    files = results.get("files", [])
    if not files:
        return None, None

    file_pattern = re.compile(r"data_bukit_vista_(\d{2}-\d{2}-\d{4})\.xlsx")
    latest_file = None
    latest_date = None

    for file in files:
        match = file_pattern.match(file["name"])
        if match:
            file_date = datetime.datetime.strptime(match.group(1), "%d-%m-%Y")
            if latest_date is None or file_date > latest_date:
                latest_date = file_date
                latest_file = file

    if latest_file:
        return latest_file["id"], latest_file["name"]
    else:
        return None, None

# === Fungsi untuk Mengunduh dan Membaca File Terbaru ===
@st.cache_data
def load_latest_data(folder_id):
    file_id, file_name = get_latest_file(folder_id)
    if file_id is None:
        return None

    drive_service = get_drive_service()
    if drive_service is None:
        return None

    request = drive_service.files().get_media(fileId=file_id)
    file_content = io.BytesIO(request.execute())
    df = pd.read_excel(file_content, dtype={"price_info": str})
    return df, file_name

# === Load Data dari Google Drive ===
FOLDER_ID = "1zdLvHzqvv0PGJ6Bt5zhL52yxMTi845ou"
result = load_latest_data(FOLDER_ID)
if result is None:
    raise ValueError("load_latest_data() returned None. Check if the folder contains the necessary files.")
df, file_name = result

if df is None:
    st.stop()

st.success(f"✅ Data berhasil dimuat dari: **{file_name}**")

# === Process DataFrame Features ===
feature_columns = [         # Menentukan kolom fitur yang digunakan untuk perhitungan
    'title_vectorizer', 'property_type_vectorizer', 
    'tags_vectorizer', 'area_vectorizer', 'price_info'
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
    return np.array(x)

# Mengonversi vektor pada semua kolom fitur kecuali 'price_info'
for col in feature_columns:
    if col != 'price_info':  # Pastikan hanya fitur lain yang diproses
        df[col] = df[col].apply(safe_eval)

# Menggabungkan semua fitur ke dalam satu array numpy
combined_features = np.array([np.hstack([row[col] for col in feature_columns if col != 'price_info']) for _, row in df.iterrows()])

# Menghitung matriks kesamaan kosinus antar properti
similarity_matrix = cosine_similarity(combined_features)

# === Property Recommendation Function ===
def recommend_properties(property_title, top_n=4):
    if property_title not in df["title"].values:
        return "Property not found"     # Mengembalikan pesan jika properti tidak ditemukan

    idx = df[df["title"] == property_title].index[0]        # Mendapatkan indeks properti yang dipilih
    similar_indices = np.argsort(similarity_matrix[idx])[::-1][1:top_n+1]       # Mendapatkan indeks properti serupa

    return df.iloc[similar_indices][["title", "image_url", "price_info", "area", "property_type"]]      # Mengembalikan hasil rekomendasi

# **Header**
st.markdown("<h1 style='text-align: center; color: black;'>Discover the Finest Vacation Rentals in Bali and Yogyakarta</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>We are here to fulfill your desire for great comfort, whether for a short-term or long-term stay in Bali or Yogyakarta.</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>The choice is yours.</p>", unsafe_allow_html=True)
st.markdown("---")      # Menambahkan garis pemisah

# **Select area from Dropdown**
selected_property_title = st.selectbox("🔎 Select Area:", df["area"].unique())       # Dropdown untuk memilih properti

# **Select Property Type from Dropdown**
selected_property_title = st.selectbox("🔎 Select Property Type:", df["property_type"].unique())       # Dropdown untuk memilih properti

# **Button to Get Recommendations**
if st.button("✨ Get Recommendations"):     # Tombol untuk mendapatkan rekomendasi
    recommended = recommend_properties(selected_property_title)

    if isinstance(recommended, str):        # Jika properti tidak ditemukan, tampilkan pesan error
        st.error(recommended)
    else:
        st.markdown("<h3 style='text-align: left;'>✔ Exclusive Property Recommendations Just for You</h3>", unsafe_allow_html=True)

        # **Display results in a grid**
        cols = st.columns(2)  # Membagi tampilan ke dalam 2 kolom
        for idx, (_, row) in enumerate(recommended.iterrows()):
            with cols[idx % 2]:
                st.image(row["image_url"], width=350)  # Menampilkan gambar properti
                st.subheader(row["title"])      # Menampilkan judul properti
                st.write(f"🗺️ **Location:** {row['area']}")     # Menampilkan lokasi properti
                st.write(f"🏡 **Type:** {row['property_type']}")        # Menampilkan tipe properti
                st.write(f"💸 **Price:** {row['price_info']}")  # Menampilkan harga properti
                st.markdown("---")      # Menambahkan garis pemisah antar properti
