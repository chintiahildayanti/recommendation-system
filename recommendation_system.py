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

# === Setup Google Drive API Credentials ===
@st.cache_resource
def get_drive_service():
    try:
        # Ambil kredensial dari Streamlit secrets
        credentials_info = json.loads(st.secrets["gdrive"]["credentials"])
        creds = service_account.Credentials.from_service_account_info(credentials_info)
        service = build("drive", "v3", credentials=creds)
        return service
    except Exception as e:
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
        return None, None

    drive_service = get_drive_service()
    if drive_service is None:
        return None, None

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
def recommend_properties(selected_area, selected_property_type, top_n=4):
    # Filter dataset berdasarkan area dan property type
    filtered_df = df[(df["area"] == selected_area) & (df["property_type"] == selected_property_type)]

    if filtered_df.empty:
        return "No properties found for this selection"

    # Menggunakan properti pertama sebagai referensi untuk rekomendasi
    reference_index = filtered_df.index[0]
    similar_indices = np.argsort(similarity_matrix[reference_index])[::-1][1:top_n+1]

    return df.iloc[similar_indices][["title", "image_url", "price_info", "area", "property_type"]]

# **Header**
st.markdown("<h1 style='text-align: center; color: black;'>Discover the Finest Vacation Rentals in Bali and Yogyakarta</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>We are here to fulfill your desire for great comfort, whether for a short-term or long-term stay in Bali or Yogyakarta.</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>The choice is yours.</p>", unsafe_allow_html=True)
st.markdown("---")      # Menambahkan garis pemisah

# **Dropdown untuk memilih Area dan Property Type**
selected_area = st.selectbox("📍 Select Area:", df["area"].unique())
selected_property_type = st.selectbox("🏠 Select Property Type:", df["property_type"].unique())

# **Button to Get Recommendations**
if st.button("✨ Get Recommendations"):
    recommended = recommend_properties(selected_area, selected_property_type)

    if isinstance(recommended, str):  # Jika properti tidak ditemukan, tampilkan pesan error
        st.error(recommended)
    else:
        st.markdown("<h3 style='text-align: left;'>✔ Exclusive Property Recommendations Just for You</h3>", unsafe_allow_html=True)

        # **Display results in a grid**
        cols = st.columns(2)  # Membagi tampilan ke dalam 2 kolom
        for idx, (_, row) in enumerate(recommended.iterrows()):
            with cols[idx % 2]:
                st.image(row["image_url"], width=350)
                st.subheader(row["title"])
                st.write(f"🗺️ **Location:** {row['area']}")
                st.write(f"🏡 **Type:** {row['property_type']}")
                st.write(f"💸 **Price:** {row['price_info']}")