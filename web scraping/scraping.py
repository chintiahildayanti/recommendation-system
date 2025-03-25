"""1. Import library yang dibutuhkan"""
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from zipfile import ZipFile
from datetime import datetime
import requests
import time
import os
import re
import numpy as np
import pandas as pd
pd.options.display.max_colwidth = 50000
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
import string
import pickle
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from tensorflow.keras.preprocessing.text import Tokenizer
# from google.colab import files
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('stopwords')
nltk.download('punkt_tab')

"""2. Scraping Title & Image Urls"""

# fungsi untuk scrapping URL gambar dari halaman web
def scrape_images(base_url, pages, img_tag, img_attr, container_class='d-flex align-items-center h-100'):
    image_urls = []   # List untuk menyimpan URL gambar
    for page in range(1, pages + 1):    # Loop melalui setiap halaman yang ingin di-scrape
        url = f"{base_url}/page/{page}"   # Menyusun URL untuk setiap halaman
        response = requests.get(url)    # Mengirimkan request HTTP ke halaman
        soup = BeautifulSoup(response.text, 'html.parser')    # Menggunakan BeautifulSoup untuk parsing HTML
        div_containers = soup.find_all('div', attrs={'class': container_class})    # Menemukan semua elemen div yang memiliki kelas CSS yang ditentukan
        for container in div_containers:    # Loop untuk setiap div yang ditemukan untuk mengekstrak gambar
            img = container.find(img_tag)   # Mencari tag gambar dalam div
            if img and img.has_attr(img_attr):    # Memastikan tag gambar memiliki atribut yang diinginkan
                image_urls.append(img[img_attr])    # Menambahkan URL gambar ke dalam list
    return image_urls   # Mengembalikan list URL gambar yang ditemukan

# Fungsi untuk scrapping judul properti dari halaman web
def scrape_property_title(base_url, pages, field_class, container_class='d-flex align-items-center h-100'):
    data = []   # List untuk menyimpan judul properti
    for page in range(1, pages + 1):    # Loop untuk setiap halaman
        url = f"{base_url}/page/{page}"   # Menyusun URL untuk setiap halaman
        response = requests.get(url)    # Mengirimkan request ke halaman
        soup = BeautifulSoup(response.text, 'html.parser')    # Parsing HTML
        div_containers = soup.find_all('div', attrs={'class': container_class})  # Menemukan semua kontainer
        for container in div_containers:    # Loop untuk setiap kontainer
            field = container.find(attrs={'class': field_class})    # Menemukan elemen dengan kelas field_class
            data.append(field.text.strip() if field else None)    # Menambahkan judul ke dalam list
    return data   # Mengembalikan daftar judul properti

# Scraping data untuk properti di berbagai lokasi
locations = {
    "Bali": "https://www.bukitvista.com/city/bali",
    "Nusa Penida": "https://www.bukitvista.com/city/nusa-penida",
    "Yogyakarta": "https://www.bukitvista.com/city/yogyakarta",
}

# List untuk menyimpan data properti dari semua lokasi
all_properties = []

# Looping melalui setiap lokasi untuk melakukan scraping
for location, url in locations.items():
    titles = scrape_property_title(url, 5, 'item-title')    # Scraping judul properti
    image_urls = scrape_images(url, 5, 'img', 'src')    # Scraping URL gambar properti

    # Membuat DataFrame untuk menyimpan data properti di berbagai lokasi
    property_df = pd.DataFrame({
        'title': titles,          # Kolom untuk judul properti
        'image_url': image_urls   # Kolom untuk URL gambar properti
    })

    all_properties.append(property_df)    # Menambahkan DataFrame ke dalam list

# Menggabungkan semua hasil scraping dari berbagai lokasi menjadi satu DataFrame
images_title_df = pd.concat(all_properties, axis=0).reset_index(drop=True)

# Menampilkan DataFrame hasil scraping
images_title_df

"""3. Scraping Property "Uluwatu Modern Boho Villa Near Nyang Nyang Beach"""

# Scraping data untuk properti "Uluwatu Modern Boho Villa Near Nyang Nyang Beach"
uluwatu_property = pd.DataFrame({
    'title': scrape_property_title('https://www.bukitvista.com/property-type/island-life', 1, 'item-title'),    # Scraping judul properti
    'tags': scrape_property_title('https://www.bukitvista.com/property-type/island-life', 1, 'labels-wrap labels-right'),   # Scraping kategori/tag properti
    'price': scrape_property_title('https://www.bukitvista.com/property-type/island-life', 1, 'item-price item-price-text'),    # Scraping harga properti
    'property_type': scrape_property_title('https://www.bukitvista.com/property-type/island-life', 1, 'h-type'),    # Scraping tipe properti
    'address_detail': scrape_property_title('https://www.bukitvista.com/property-type/island-life', 1, 'item-address'),   # Scraping alamat properti
})
# Menampilkan jumlah properti yang berhasil di-scrape
print('Total properties:', len(uluwatu_property))

# Menampilkan DataFrame
uluwatu_property

# Hanya mengambil data property "Uluwatu Modern Boho Villa Near Nyang Nyang Beach"
uluwatu_property = uluwatu_property[uluwatu_property['title'] != "Bingin Beach Hideaway: Group Villa with Pool & BBQ"]

"""4. Scraping URL"""

# fungsi untuk scraping href yang berada di "https://www.bukitvista.com/property/"
def scrape_property_links(url: str) -> pd.DataFrame:
    # Membuat instance dari Chrome WebDriver dengan konfigurasi khusus
    option = webdriver.ChromeOptions()
    option.add_argument("--start-maximized")  # Membuka jendela browser Chrome dalam mode layar penuh
    option.add_argument("--headless")   # Menjalankan browser dalam mode tanpa antarmuka grafis
    option.add_argument("--disable-gpu")  # Menonaktifkan akselerasi GPU
    option.add_argument("--no-sandbox")   # Menonaktifkan sandbox untuk keamanan
    option.add_argument("--remote-debugging-port=56905")   # Mengaktifkan debugging jarak jauh pada port 9230
    driver = webdriver.Chrome(options=option)

    # Memuat halaman
    driver.get(url)

    # Tunggu halaman termuat
    time.sleep(3)

    # List untuk menyimpan url properti
    links = []

    # Loop untuk navigasi pagination
    while True:
        # Ambil semua tautan properti di halaman saat ini
        property_links = driver.find_elements(By.XPATH, '//a[contains(@href, "/property/")]')

        # Iterasi melalui setiap elemen link dalam daftar 'property_links'
        for link in property_links:
            # Ambil nilai atribut 'href' dari elemen <a>
            href = link.get_attribute("href")
            # Hanya tambahkan tautan unik dan hindari tautan ke halaman navigasi
            if href and href not in links and "page" not in href:
                links.append(href)

        # Coba cari tombol 'Next' untuk navigasi ke halaman berikutnya
        try:
            next_button = driver.find_element(By.XPATH, '//a[contains(@aria-label, "Next")]')
            next_button.click()
            time.sleep(3)  # Tunggu halaman berikutnya termuat
        except:
            # Jika tombol 'Next' tidak ditemukan, berarti sudah di halaman terakhir
            break

    # Masukkan tautan ke DataFrame
    df = pd.DataFrame(links, columns=["property_links"])

    # Menghapus url https://www.bukitvista.com/property/ dari DataFrame
    df = df[df["property_links"] != "https://www.bukitvista.com/property/"].reset_index(drop=True)

    # Tutup driver
    driver.quit()

    # Menampilkan jumlah url yang berhasil di-scrape
    print('Total url:', len(df))

    # Mengembalikan DataFrame yang berisi links
    return df

# Definisikan url
bukit_vista_url = "https://www.bukitvista.com/property/"

# Panggil dan terapkan fungsi
url_df = scrape_property_links(bukit_vista_url)

"""5. Scraping Title, Address & Tags"""

# Fungsi untuk melakukan scraping data properti dari URL
def scrape_property_combined(url_df, container_class='container'):
    # List untuk menyimpan data hasil scraping
    data = []

    # Iterasi setiap URL dalam kolom 'property_links' pada DataFrame
    for url in url_df["property_links"]:
        try:
            # Melakukan permintaan HTTP GET ke URL
            response = requests.get(url, timeout=30)

            # Memastikan permintaan berhasil
            response.raise_for_status()

            # Parsing HTML dari respons menggunakan BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Mencari semua elemen <div> dengan atribut 'class' yang sesuai
            div_containers = soup.find_all('div', attrs={'class': container_class})

            # Inisialisasi variabel untuk menyimpan data yang akan diambil
            title = None
            address = None
            tags = None

            # Iterasi melalui setiap container untuk mengekstrak data
            for container in div_containers:
                # Mencari elemen dengan kelas 'page-title' untuk judul properti
                if title is None:
                    title_element = container.find(attrs={'class': 'page-title'})
                    # Ambil teks dari elemen jika ditemukan, jika tidak, tetap None
                    title = title_element.text.strip() if title_element else None

                # Mencari elemen dengan kelas 'item-address' untuk alamat properti
                if address is None:
                    address_element = container.find(attrs={'class': 'item-address'})
                    # Ambil teks dari elemen jika ditemukan, jika tidak, tetap None
                    address = address_element.text.strip() if address_element else None

                # Mencari elemen dengan kelas 'property-labels-wrap' untuk label properti
                if tags is None:
                    tags_element = container.find(attrs={'class': 'property-labels-wrap'})
                    # Ambil teks dari elemen jika ditemukan, jika tidak, tetap None
                    tags = tags_element.text.strip() if tags_element else None

            # Tambahkan data hasil scraping ke list dalam bentuk dictionary
            data.append({'title': title, 'address': address, 'tags': tags})

        # Menangkap error yang terjadi saat melakukan permintaan HTTP
        except requests.RequestException as e:
            # Cetak pesan error dan URL yang bermasalah
            print(f"Error accessing URL {url}: {e}")
            # Tambahkan data kosong untuk URL yang gagal
            data.append({'title': None, 'address': None, 'tags': None})

    # Mengembalikan data hasil scraping dalam bentuk DataFrame
    return pd.DataFrame(data)

# Scrape semua data properti dari DataFrame 'url_df'
property_data = scrape_property_combined(url_df)

"""6. Scraping Property Details"""

# Fungsi untuk melakukan scraping berdasarkan elemen <strong> dan <span>
def property_details(url, container_class='detail-wrap'):
    # Dictionary untuk menyimpan data hasil scraping
    data = {}

    # Melakukan permintaan HTTP GET ke URL
    response = requests.get(url)

    # Parsing HTML dari respons menggunakan BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Mencari container utama
    div_container = soup.find('div', class_=container_class)
    if div_container:
        # Mencari semua elemen <li>
        fields = div_container.find_all('li')
        for field in fields:
            # Mengambil teks dari elemen <strong> dan <span>
            strong = field.find('strong')
            span = field.find('span')
            if strong and span:
                # Standarisasi nama kolom
                column_name = standardize_column_name(strong.text.strip())
                data[column_name] = span.text.strip()  # Nilai berdasarkan <span>

    # Mengembalikan data hasil scrapping
    return data

# Fungsi untuk standarisasi nama kolom
def standardize_column_name(column_name):
    # Ubah nama kolom menjadi lowercase
    column_name = column_name.lower()
    # Ganti bentuk jamak dengan bentuk singular (bedrooms -> bedroom, dll.)
    replacements = {
        'bedrooms': 'bedroom',
        'bathrooms': 'bathroom',
        'rooms': 'room'
    }

    # Looping melalui semua pasangan key-value dalam dictionary `replacements`
    for key, value in replacements.items():
        # Mengganti setiap kemunculan 'key' dalam 'column_name' dengan 'value'
        column_name = column_name.replace(key, value)

    # Hapus karakter tidak diinginkan seperti ':', spasi ekstra, atau simbol lainnya
    column_name = ''.join(char for char in column_name if char.isalnum() or char == ' ')
    column_name = column_name.strip().replace(' ', '_')  # Ganti spasi dengan underscore

    # Mengembalikan 'column_name' yang telah diperbarui setelah semua penggantian selesai
    return column_name

# DataFrame untuk menyimpan hasil scraping
all_properties = []

# Loop melalui setiap URL dalam url_df
for index, row in url_df.iterrows():
    # Mengambil URL dari kolom 'property_links' pada baris saat ini
    url = row['property_links']
    # Memanggil fungsi 'property_details' untuk melakukan scraping data dari URL
    scraped_data = property_details(url)
    # Menambahkan data yang telah di-scrape ke dalam list 'all_properties'
    all_properties.append(scraped_data)

# Membuat DataFrame akhir
detail_properties = pd.DataFrame(all_properties)

"""7. Scraping Property Description"""

# Fungsi untuk scraping property description
def scrape_property_descriptions(urls):
  # List untuk menyimpan data hasil scraping
  results = []

  # Iterasi melalui setiap URL dalam kolom 'property_links'
  for url in url_df["property_links"]:
      # Mengirim permintaan ke halaman website
      response = requests.get(url)

      # Parsing HTML dari respons menggunakan BeautifulSoup
      soup = BeautifulSoup(response.text, 'html.parser')

      # Membatasi pencarian hanya pada container 'block-content-wrap'
      container = soup.find('div', class_='block-content-wrap')

      # Mengecek apakah container ditemukan
      if container:
          # Inisialisasi struktur data untuk menyimpan hasil
          data = []
          current_header = None

          # Iterasi melalui elemen-elemen dalam container
          for element in container.find_all(['h1', 'h2', 'h3', 'p', 'li']):
              if element.name in ['h1', 'h2', 'h3']:
                  # Menetapkan header baru jika elemen adalah h1, h2, atau h3
                  current_header = element.text.strip().lower()
              elif element.name in ['p', 'li']:
                  # Menambahkan teks dari elemen 'p' atau 'li' ke data
                  if current_header:
                      # Jika ada header, tambahkan ke data dengan header yang relevan
                      data.append({"header": current_header, "text": element.text.strip()})
                  else:
                      # Jika tidak ada header sebelumnya, gunakan 'others' sebagai header default
                      data.append({"header": "others", "text": element.text.strip()})

          # Memproses data menjadi dictionary yang mengelompokkan teks berdasarkan header
          df_dict = {}
          # Iterasi melalui setiap elemen dalam daftar 'data'
          for item in data:
              # Memeriksa apakah value dalam key 'header' dari 'item' belum ada dalam dictionary 'df_dict'
              if item["header"] not in df_dict:
                  # Menambahkan header baru jika belum ada dalam dictionary
                  df_dict[item["header"]] = []
              # Menambahkan teks untuk header yang sesuai
              df_dict[item["header"]].append(item["text"])

          # Menggabungkan isi kolom menjadi satu string untuk setiap kolom (header)
          df_dict = {key: "\n\n".join(values) for key, values in df_dict.items()}

          # Menambahkan hasil ke daftar
          results.append(df_dict)
      else:
          # Jika container tidak ditemukan, cetak pesan error dan tambahkan dictionary kosong
          print(f"Container tidak ditemukan untuk URL: {url}")
          results.append({})  # Tambahkan dictionary kosong jika container tidak ditemukan

  # Mengembalikan DataFrame hasil
  return pd.DataFrame(results)

# Menerapkan fungsi
property_description = scrape_property_descriptions(url_df["property_links"])

"""8. Scraping Address Details"""

# Fungsi untuk melakukan scraping data address dari URL
def address_details(url_df, container_class='list-2-cols list-unstyled'):
    # List untuk menyimpan data hasil scraping
    data = []

    # Iterasi setiap URL dalam kolom 'property_links' pada DataFrame
    for url in url_df["property_links"]:
        try:
            # Melakukan permintaan HTTP GET ke URL
            response = requests.get(url, timeout=30)

            # Memastikan permintaan berhasil
            response.raise_for_status()

            # Parsing HTML dari respons menggunakan BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Mencari elemen <ul> dengan class container_class yang sesuai
            ul_container = soup.find('ul', attrs={'class': container_class})

            # Inisialisasi variabel untuk menyimpan data yang akan diambil
            address = None
            city = None
            state = None
            zip_code = None
            area = None
            country = None

            # Jika <ul> ditemukan, lanjutkan mencari elemen <span> dalam <li> tertentu
            if ul_container:
                # Mencari elemen <li> dengan kelas tertentu dan ambil teks dari <span>
                for li in ul_container.find_all('li'):
                    span_element = li.find('span')
                    if span_element:
                        # Tentukan data berdasarkan class dari <li> untuk penandaan
                        if 'detail-address' in li.get('class', []):
                            address = span_element.text.strip()
                        elif 'detail-city' in li.get('class', []):
                            city = span_element.text.strip()
                        elif 'detail-state' in li.get('class', []):
                            state = span_element.text.strip()
                        elif 'detail-zip' in li.get('class', []):
                            zip_code = span_element.text.strip()
                        elif 'detail-area' in li.get('class', []):
                            area = span_element.text.strip()
                        elif 'detail-country' in li.get('class', []):
                            country = span_element.text.strip()

            # Tambahkan data hasil scraping ke list dalam bentuk dictionary
            data.append({'address_detail': address, 'city': city, 'state': state, 'zip_code': zip_code, 'area': area, 'country': country})

        # Menangkap error yang terjadi saat melakukan permintaan HTTP
        except requests.RequestException as e:
            # Cetak pesan error dan URL yang bermasalah
            print(f"Error accessing URL {url}: {e}")
            # Tambahkan data kosong untuk URL yang gagal
            data.append({'address_detail': None, 'city': None, 'state': None, 'zip_code': None, 'area': None, 'country': None})

    # Mengembalikan data hasil scraping dalam bentuk DataFrame
    return pd.DataFrame(data)

# Scrape semua data properti dari DataFrame 'url_df'
property_address_details = address_details(url_df)

"""9. Concat The DataFrame"""

# Fungsi untuk menggabungkan beberapa DataFrame properti Bukit Vista, membersihkan data kosong, dan menambahkan URL gambar berdasarkan judul properti.
def process_bukit_vista_data(url_df, property_data, detail_properties, property_address_details,
                              uluwatu_property, images_title_df):

  # Menggabungkan beberapa DataFrame yang diperlukan
  bukit_vista_property = pd.concat([url_df, property_data, detail_properties, property_address_details], axis=1)

  # Mengecek jumlah data duplikat berdasarkan kolom 'title' dan 'property_id'
  duplicates_data = bukit_vista_property.duplicated(subset=['title','property_id']).sum()

  # Menampilkan jumlah duplikat yang ditemukan
  print(f"Jumlah duplikat berdasarkan title: {duplicates_data}")

  # Menghapus data duplikat berdasarkan kolom 'title' dan 'property_id', menyimpan entri pertama dan menghapus yang lainnya
  bukit_vista_property = bukit_vista_property.drop_duplicates(subset=['title','property_id'], keep='first')

  # Mengganti nilai kosong ('') dengan NaN pada beberapa kolom untuk mempermudah identifikasi
  for col in ['title', 'tags', 'address_detail']:
      if col in bukit_vista_property.columns:
          bukit_vista_property[col] = bukit_vista_property[col].replace('', np.nan)

 # Mengisi data yang kosong pada baris pertama menggunakan data dari uluwatu_property jika tersedia
  if not uluwatu_property.empty:
    first_row_uluwatu = uluwatu_property.iloc[0]    # Ambil baris pertama dari uluwatu_property
    bukit_vista_property.iloc[0] = bukit_vista_property.iloc[0].fillna(first_row_uluwatu)   # Isi NaN dengan data ini

  # Menggabungkan kolom image_url dari images_title_df ke bukit_vista_property berdasarkan kolom title
  if 'title' in images_title_df.columns and 'title' in bukit_vista_property.columns:
    bukit_vista_property = bukit_vista_property.merge(
        images_title_df[['title', 'image_url']],  # Pilih hanya kolom 'title' dan 'image_url'
        on='title',  # Gabungkan berdasarkan kolom title
        how='left'  # Gunakan 'left' agar data di bukit_vista_property tetap ada
    )

  # Mengembalikan DataFrame hasil penggabungan
  return bukit_vista_property

# Memanggil fungsi untuk memproses data Bukit Vista
bukit_vista_property = process_bukit_vista_data(url_df, property_data, detail_properties,
                                                property_address_details, uluwatu_property, images_title_df)

# Fungsi untuk menambahkan kolom 'title' dari bukit_vista_property ke property_description berdasarkan urutan
def add_title_to_description(property_description, bukit_vista_property):
    return property_description.assign(title=bukit_vista_property['title']) # Mengembalikan property_description

# Memanggil fungsi
property_description = add_title_to_description(property_description, bukit_vista_property)

"""10. Data Cleaning"""

# Fungsi untuk mengisi kolom 'tags' berdasarkan informasi 'address_detail'
def fill_tags(row):
    if pd.isna(row['tags']):    # Mengecek apakah kolom 'tags' bernilai NaN (kosong)
        address_detail = str(row['address_detail']).lower()   # Mengambil detail alamat dan mengubahnya menjadi huruf kecil untuk perbandingan
        # Menentukan nilai 'tags' berdasarkan kata kunci dalam 'address_detail'
        if "bali" in address_detail:    # Jika mengandung kata "bali"
            return "Bali Vacation Rental"
        elif "nusa penida" in address_detail:   # Jika mengandung kata "nusa penida"
            return "Nusa Penida Vacation Rental"
        elif "yogyakarta" in address_detail:    # Jika mengandung kata "yogyakarta"
            return "Yogyakarta Vacation Rental"
    return row['tags']    # Jika 'tags' sudah diisi atau tidak ada kata kunci yang cocok, kembalikan nilai asli

# Fungsi untuk mengklasifikasikan jenis properti berdasarkan kata-kata kunci tertentu yang terdapat dalam 'property_type'
def extract_class_property(property_type):
    # Mengubah nilai property_type menjadi huruf kecil agar pencocokan tidak sensitif terhadap kapitalisasi
    property_type = property_type.lower()
    # Memeriksa apakah kata 'guest house' terdapat dalam property_type
    if 'guest house' in property_type:
        return 'guest house'
    # Memeriksa apakah kata 'residential' terdapat dalam property_type
    elif 'residential' in property_type:
        return 'residential'
    # Memeriksa apakah kata 'villa' terdapat dalam property_type
    elif 'villa' in property_type:
        return 'villa'
    # Jika tidak ada kecocokan, kembalikan None
    return None

# Inisialisasi stopwords
stop_words = set(stopwords.words('english'))
# Inisialisasi stemmer
ps = PorterStemmer()
# Inisialisasi lemmatizer
lemmatizer = WordNetLemmatizer()

# Fungsi untuk membersihkan teks dan mempersiapkannya untuk tokenisasi dan vektorisasi
def preprocess_text(text):
    # Mengubah teks menjadi huruf kecil
    text = text.lower()
    # Menghapus spasi kosong di awal dan akhir teks
    text = text.strip()
    # Hapus URL, username, dan karakter non-alphanumeric -> regex
    text = re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", " ", text)
    # Hapus angka
    text = re.sub(r"\d+", "", text)
    # Hapus karakter spesial
    text = text.translate(str.maketrans('', '', string.punctuation))
    # Memecah teks menjadi kata-kata (tokenisasi)
    tokens = word_tokenize(text)
    # Lematisasi untuk mendapatkan bentuk dasar kata
    tokens = [lemmatizer.lemmatize(word) for word in tokens]
    # Menghapus kata-kata yang dianggap tidak penting (stopwords)
    tokens = [word for word in tokens if word not in stop_words]
    # Mengubah kata menjadi bentuk dasarnya menggunakan stemming
    tokens = [ps.stem(word) for word in tokens]
    # Gabungkan kembali tokens menjadi teks
    text = ' '.join(tokens)
    # Mengembalikan text
    return text

# Fungsi untuk membersihkan teks dalam kolom 'tags'
def clean_tags(text):
    # Ganti semua pola "\n\t" atau kombinasi "\n" dan "\t" dengan spasi
    text = re.sub(r"\s+", " ", text)  # Menghapus semua whitespace berlebih
    text = text.strip()  # Menghapus whitespace di awal dan akhir teks
    return text   # Mengembalikan text

# Fungsi untuk membersihkan teks dalam kolom 'property_id'
def clean_property_id(text):
    text = text.lower()  # Mengubah teks menjadi huruf kecil
    text = text.strip()  # Menghapus whitespace di awal dan akhir teks
    return text  # Mengembalikan text

# Fungsi untuk mengekstrak harga dari teks dalam format USD ($) atau Rupiah (Rp)
def extract_price(text):
  # Mengecek apakah teks mengandung mata uang USD
  if 'USD' in text or '$' in text:
    # Mencari angka dalam format USD
    usd_match = re.search(r'(\d+[\.,]?\d*)', text)
    if usd_match:
      # Mengubah angka ke float setelah menghapus tanda koma (,) sebagai pemisah ribuan
      return float(usd_match.group(1).replace(',', ''))

  # Mengecek apakah teks mengandung mata uang Rupiah (Rp)
  elif 'Rp' in text:
    # Mencari angka dalam format Rupiah
    rp_match = re.search(r'Rp\s*([\d\.]+)', text)
    if rp_match:
      # Menghapus titik (.) sebagai pemisah ribuan dan mengonversi ke float
      rupiah = float(rp_match.group(1).replace('.', ''))
      # Mengonversi harga dari Rupiah ke USD
      return np.ceil(rupiah / 16244)

  # Jika tidak ada angka yang cocok, kembalikan NaN
  return np.nan

# Fungsi untuk mengisi kolom 'area' berdasarkan informasi 'address_detail'
def fill_area(row):
    if pd.isna(row['area']):    # Mengecek apakah kolom 'area' bernilai NaN (kosong)
        # Menentukan nilai 'area' berdasarkan kata kunci dalam 'address_detail'
        address_detail = str(row['address_detail'])
        if "Uluwatu" in address_detail:    # Jika mengandung kata "Uluwatu"
            return "Uluwatu"
        elif "Yogyakarta" in address_detail:    # Jika mengandung kata "Yogyakarta"
            return "Yogyakarta"
        elif "Pecatu" in address_detail:    # Jika mengandung kata "Pecatu"
            return "Pecatu"
    return row['area']    # Jika 'area' sudah diisi atau tidak ada kata kunci yang cocok, kembalikan nilai asli

# Fungsi untuk cleaning data
def data_cleaning(bukit_vista_property):
    # ============== Data Cleaning =========================
  # Mengisi nilai yang hilang (NaN) pada kolom 'property_type' dengan 'Villa'
  bukit_vista_property['property_type'] = bukit_vista_property['property_type'].fillna('Villa')

  # Mengisi nilai yang hilang (NaN) pada kolom 'property_id' dengan '0'
  bukit_vista_property['property_id'] = bukit_vista_property['property_id'].fillna('0')

  # Merubah isi kolom yang hanya mengandung 'View' menjadi 'Villa' untuk mengelompokkan hasil scraping images
  bukit_vista_property['property_type'] = bukit_vista_property['property_type'].apply(
    lambda x: 'Villa' if isinstance(x, str) and 'View' in x else x
  )

  # Mengisi nilai yang hilang (NaN) pada kolom 'address_detail' dengan 'Uluwatu, Bali'
  bukit_vista_property['address_detail'] = bukit_vista_property['address_detail'].fillna('Uluwatu, Bali')

  # Mengisi nilai yang hilang (NaN) pada kolom 'price' dengan 'Start from $65 USD per night'
  bukit_vista_property['price'] = bukit_vista_property['price'].fillna('Start from $65 USD per night')

  # Mengisi nilai yang hilang (NaN) pada kolom 'image_url'
  santorini_images ='https://bukitvista-wordpress-storage.s3.us-east-2.amazonaws.com/wp-content/uploads/2021/03/Santorini-Surfer-Loft-in-Uluwatu-Digital-Nomads-by-Bukit-Vista-2.jpg'
  bukit_vista_property['image_url'] = bukit_vista_property['image_url'].fillna(santorini_images)

  # Mengganti nilai kosong ('') pada kolom 'tags' dengan NaN untuk mempermudah identifikasi nilai kosong
  bukit_vista_property['tags'] = bukit_vista_property['tags'].replace('', np.nan)

  # Terapkan fungsi ke DataFrame kolom 'tags'
  bukit_vista_property['tags'] = bukit_vista_property.apply(fill_tags, axis=1)

  # Menambahkan kolom baru 'class' untuk mengelompokkan hasil scraping images
  bukit_vista_property['class'] = bukit_vista_property['property_type'].apply(extract_class_property)

  # Mengganti nilai kosong ('') pada kolom 'area' dengan NaN untuk mempermudah identifikasi nilai kosong
  bukit_vista_property['area'] = bukit_vista_property['area'].replace('', np.nan)

  # Terapkan fungsi untuk mengisi area
  bukit_vista_property['area'] = bukit_vista_property.apply(fill_area, axis=1)

  # Ubah kolom 'area' ke string setelah pengisian selesai
  bukit_vista_property['area'] = bukit_vista_property['area'].astype(str)

  # Copy DataFrame sebelum data cleaning, tokenisasi dan vektorisasi
  bukit_vista_df = bukit_vista_property.copy()

  # Terapkan fungsi preprocess_text pada kolom title
  bukit_vista_df['cleaned_title'] = bukit_vista_df['title'].apply(preprocess_text)

  # Terapkan fungsi preprocess_text pada kolom property_type
  bukit_vista_df['cleaned_property_type'] = bukit_vista_df['property_type'].apply(preprocess_text)

  # Terapkan fungsi preprocess_text pada kolom address_detail
  bukit_vista_df['address_detail'] = bukit_vista_df['address_detail'].apply(preprocess_text)

  # Terapkan fungsi clean_tags pada kolom tags
  bukit_vista_df['tags'] = bukit_vista_df['tags'].apply(clean_tags)

  # Terapkan fungsi preprocess_text pada kolom tags
  bukit_vista_df['tags'] = bukit_vista_df['tags'].apply(preprocess_text)

  # Terapkan fungsi preprocess_text pada kolom area
  bukit_vista_df['cleaned_area'] = bukit_vista_df['area'].apply(preprocess_text)

  # Terapkan fungsi clean_property_id pada kolom property_id
  bukit_vista_df['property_id'] = bukit_vista_df['property_id'].apply(clean_property_id)

  # Mengganti simbol '/' dengan ' per ' dalam kolom 'price'
  bukit_vista_df['price'] = bukit_vista_df['price'].str.replace("/", " per ")

  # Menerapkan fungsi extract_price untuk mengekstrak harga dalam bentuk angka
  bukit_vista_df['price_in_usd'] = bukit_vista_df['price'].apply(lambda x: extract_price(x)).astype(str)

  # Mengekstrak periode sewa dari teks, yaitu kata setelah "per"
  bukit_vista_df['rental_period'] = bukit_vista_df['price'].str.extract(r'per (.+)$')

  # Jika tidak ditemukan periode sewa (NaN), maka diisi dengan nilai default 'night'
  bukit_vista_df['rental_period'] = bukit_vista_df['rental_period'].fillna('night')

  # Ubah ke lowercase dulu, lalu ganti "malam" dengan "night"
  bukit_vista_df['rental_period'] = bukit_vista_df['rental_period'].str.lower().str.strip().str.replace('malam', 'night', regex=True)

  # Gabungkan kolom price_in_usd dan rental_period ke dalam kolom baru dengan format "starting from $84.0 per night"
  bukit_vista_df['price_info'] = "Starting from $" + bukit_vista_df['price_in_usd'].astype(str) + " per " + bukit_vista_df['rental_period']

  # Mengembalikan bukit_vista_df
  return bukit_vista_df

# Menerapkan fungsi data_cleaning
bukit_vista_df = data_cleaning(bukit_vista_property)

"""11. Vectorizer"""

# Mendefinisikan fungsi vectorizer
def vectorizer(bukit_vista_df):
  # Inisialisasi TF-IDF Vectorizer
  title_vectorizer = TfidfVectorizer(min_df=5,
                              max_df=0.8,
                              sublinear_tf=True,
                              use_idf=True)

  property_type_vectorizer = TfidfVectorizer(min_df=5,
                              max_df=0.8,
                              sublinear_tf=True,
                              use_idf=True)

  tags_vectorizer = TfidfVectorizer(min_df=5,
                              max_df=0.8,
                              sublinear_tf=True,
                              use_idf=True)

  address_detail_vectorizer = TfidfVectorizer(min_df=5,
                              max_df=0.8,
                              sublinear_tf=True,
                              use_idf=True)

  area_vectorizer = TfidfVectorizer(min_df=5,
                              max_df=0.8,
                              sublinear_tf=True,
                              use_idf=True)

  # Vektorisasi teks pada kolom 'title' menggunakan TF-IDF
  title_tfidf_matrix = title_vectorizer.fit_transform(bukit_vista_df['cleaned_title'])

  # Vektorisasi teks pada kolom 'property_type' menggunakan TF-IDF
  property_type_tfidf_matrix = property_type_vectorizer.fit_transform(bukit_vista_df['cleaned_property_type'])

  # Vektorisasi teks pada kolom 'tags' menggunakan TF-IDF
  tags_tfidf_matrix = tags_vectorizer.fit_transform(bukit_vista_df['tags'])

  # Vektorisasi teks pada kolom 'address_detail' menggunakan TF-IDF
  address_detail_tfidf_matrix = address_detail_vectorizer.fit_transform(bukit_vista_df['address_detail'])

  # Vektorisasi teks pada kolom 'area' menggunakan TF-IDF
  area_tfidf_matrix = area_vectorizer.fit_transform(bukit_vista_df['cleaned_area'])

  # Mengonversi hasil TF-IDF dari bentuk matriks sparse ke dalam list, lalu menyimpannya di dataframe
  bukit_vista_df['title_vectorizer'] = title_tfidf_matrix.toarray().tolist()
  bukit_vista_df['property_type_vectorizer'] = property_type_tfidf_matrix.toarray().tolist()
  bukit_vista_df['tags_vectorizer'] = tags_tfidf_matrix.toarray().tolist()
  bukit_vista_df['address_detail_vectorizer'] = address_detail_tfidf_matrix.toarray().tolist()
  bukit_vista_df['area_vectorizer'] = area_tfidf_matrix.toarray().tolist()

  # Mengembalikan bukit_vista_df
  return bukit_vista_df

# Menerapkan fungsi
bukit_vista_df = vectorizer(bukit_vista_df)

"""12. Tokenizer"""

# Mendefinisikan fungsi tokenizer
def tokenizer(bukit_vista_df):
  # Inisialisasi tokenizer
  tokenizer_title = Tokenizer()
  tokenizer_property_type = Tokenizer()
  tokenizer_tags = Tokenizer()
  tokenizer_address_detail = Tokenizer()
  tokenizer_price = Tokenizer()
  tokenizer_property_id = Tokenizer()
  tokenizer_area = Tokenizer()

  # Membuat tokenizer untuk kolom 'title'
  title_tokenizer = tokenizer_title.fit_on_texts(bukit_vista_df['cleaned_title'])

  # Mengonversi teks dalam kolom 'title' menjadi urutan angka (sequences)
  bukit_vista_df['title_sequences'] = tokenizer_title.texts_to_sequences(bukit_vista_df['cleaned_title'])

  # Membuat tokenizer untuk kolom 'property_type'
  property_type_tokenizer = tokenizer_property_type.fit_on_texts(bukit_vista_df['cleaned_property_type'])

  # Mengonversi teks dalam kolom 'property_type' menjadi urutan angka (sequences)
  bukit_vista_df['property_type_sequences'] = tokenizer_property_type.texts_to_sequences(bukit_vista_df['cleaned_property_type'])

  # Membuat tokenizer untuk kolom 'tags'
  tags_tokenizer = tokenizer_tags.fit_on_texts(bukit_vista_df['tags'])

  # Mengonversi teks dalam kolom 'tags' menjadi urutan angka (sequences)
  bukit_vista_df['tags_sequences'] = tokenizer_tags.texts_to_sequences(bukit_vista_df['tags'])

  # Membuat tokenizer untuk kolom 'address_detail'
  address_detail_tokenizer = tokenizer_address_detail.fit_on_texts(bukit_vista_df['address_detail'])

  # Mengonversi teks dalam kolom 'address_detail' menjadi urutan angka (sequences)
  bukit_vista_df['address_detail_sequences'] = tokenizer_address_detail.texts_to_sequences(bukit_vista_df['address_detail'])

  # Membuat tokenizer untuk kolom 'price'
  price_tokenizer = tokenizer_price.fit_on_texts(bukit_vista_df['price_in_usd'])

  # Mengonversi teks dalam kolom 'price' menjadi urutan angka (sequences)
  bukit_vista_df['price_sequences'] = tokenizer_price.texts_to_sequences(bukit_vista_df['price_in_usd'])

  # Membuat tokenizer untuk kolom 'property_id'
  property_id_tokenizer = tokenizer_property_id.fit_on_texts(bukit_vista_df['property_id'])

  # Mengonversi teks dalam kolom 'property_id' menjadi urutan angka (sequences)
  bukit_vista_df['property_id_sequences'] = tokenizer_property_id.texts_to_sequences(bukit_vista_df['property_id'])

  # Membuat tokenizer untuk kolom 'area'
  area_tokenizer = tokenizer_area.fit_on_texts(bukit_vista_df['cleaned_area'])

  # Mengonversi teks dalam kolom 'area' menjadi urutan angka (sequences)
  bukit_vista_df['area_sequences'] = tokenizer_area.texts_to_sequences(bukit_vista_df['cleaned_area'])

  # Mengembalikan bukit_vista_df
  return bukit_vista_df

# Menerapkan fungsi
bukit_vista_df = tokenizer(bukit_vista_df)

"""13. Download Dataset"""

# Generate timestamp dengan format hari-bulan-tahun
timestamp = datetime.now().strftime("%d-%m-%Y")

# Simpan file dengan nama yang mengandung timestamp
bukit_vista_filename = f"data_bukit_vista_{timestamp}.xlsx"
property_description_filename = f"property_description_{timestamp}.xlsx"

bukit_vista_df.to_excel(bukit_vista_filename, index=False)
property_description.to_excel(property_description_filename, index=False)