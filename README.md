# 🏠 Sistem Rekomendasi Properti Bukit Vista

Tujuan proyek ini adalah untuk membangun sebuah aplikasi web interaktif berbasis Streamlit yang dapat merekomendasikan properti penginapan terbaik di Bali dan Yogyakarta berdasarkan preferensi pengguna. Sistem ini terintegrasi dengan Google Drive untuk secara otomatis mengambil data terbaru, memproses fitur vektorisasi, dan menggunakan kemiripan kosinus (cosine similarity) untuk memberikan rekomendasi properti paling relevan.


## 📂 Dataset
Data yang digunakan adalah data asli milik Bukit Vista yang discraping dari website Bukit Vista.
Alamat Website :
- https://www.bukitvista.com/property/ (mengambil semua data yang berada didalam HTML ini)
- https://www.bukitvista.com/property/bingin-beach-hideaway-group-villa-with-pool-amp-bbq (salah satu contoh data properti yang diambil)

---

## ✨ Fitur Utama

- 🔄 **Data otomatis diperbarui**: Mengambil file Excel terbaru secara otomatis dari folder Google Drive.
- 📊 **Pengolahan fitur**: Menggabungkan fitur vektorisasi (judul, lokasi, tipe properti dan harga) untuk menghitung kemiripan antar properti.
- 💡 **Rekomendasi cerdas**: Menggunakan cosine similarity untuk mencari properti yang mirip berdasarkan lokasi dan tipe properti yang dipilih.
- 🌐 **Antarmuka Streamlit**: UI bersih dan interaktif dengan dropdown serta tampilan rekomendasi dinamis.
- ☁️ **Integrasi Google API**: Mengakses file Google Drive secara aman menggunakan Service Account.

---

## 🛠️ Teknologi yang Digunakan

- **Python**
- **Streamlit** – untuk membangun UI web
- **Pandas & NumPy** – manipulasi dan analisis data
- **scikit-learn** – untuk perhitungan cosine similarity
- **Google Drive API** – untuk mengambil file Excel secara otomatis
