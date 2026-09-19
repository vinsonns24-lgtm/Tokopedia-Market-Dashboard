# Product Intelligence Dashboard

Riset pasar untuk calon penjual Tokopedia, dibangun dari 29.519 listing produk
dan 40.607 ulasan pembeli berbahasa Indonesia. Dashboard ini tidak hanya
menunjukkan kategori mana yang ramai, tapi juga apa yang dikeluhkan pembeli di
sana, dan seberapa bisa dipercaya setiap angkanya.

<!-- Screenshot dashboard dan link demo ditambahkan setelah deploy. -->

**Pertanyaan yang dijawab:** *"Kalau saya mau jualan di kategori ini, di segmen
harga mana celahnya, dan apa yang harus saya perbaiki dari kompetitor?"*

## Sorotan

- **Model dibawa sampai ke produk, bukan berhenti di notebook.** Klasifikasi
  sentimen dievaluasi pada produk yang tidak pernah dilihatnya, lalu dipakai di
  tab *Cek Ulasan*. Model menangkap 80% keluhan, sedangkan aturan kata kunci
  yang dipakai sebelumnya hanya punya precision 5,7%.
- **Kebocoran data diukur, bukan sekadar dihindari.** Dengan pemisahan acak, 42%
  produk muncul di data latih dan uji sekaligus, dan akurasi klasifikasi kategori
  naik semu dari 44,7% menjadi 50,3%.
- **Skor rancangan sendiri, diuji kestabilannya.** Dari 13 variasi desain dan
  300 sampel ulang (bootstrap), hanya dua segmen teratas yang kokoh. Uji ini
  juga menunjukkan skornya lebih menunjuk *pasar sepi* daripada *pasar besar*:
  7 dari 10 segmen teratas bernilai penjualan di bawah rata-rata.
- **Bug yang tidak memunculkan error.** Pencocokan potongan huruf membuat `"mur"`
  cocok dengan `"murah"`, sehingga 9,5% produk salah kategori. Sekarang dijaga
  oleh test regresi.
- **53 test otomatis** yang berjalan tanpa dataset. Salah satunya menemukan bug
  crash yang tidak pernah terpicu di pipeline.

## Isi project

### Dashboard

| Tab | Pertanyaan | Isi |
|---|---|---|
| Ringkasan Pasar | Kategori ini menarik atau tidak? | Nilai pasar, jumlah pesaing, harga median, sebaran geografis |
| Peluang Segmen | Di segmen harga mana celahnya? | Skor peluang per kategori x segmen harga, beserta seberapa stabil peringkatnya |
| Diagnostik Ulasan | Apa yang bisa saya lakukan lebih baik? | Tema keluhan per kategori, kata menonjol pada ulasan negatif |
| Cek Ulasan | Ulasan ini keluhan atau bukan? | Probabilitas dari model, tema dari aturan, dan kata yang paling menggeser keputusan model |
| Metodologi | Seberapa bisa dipercaya? | Keputusan pengolahan dan keterbatasan |

### Notebook

| Notebook | Isi | Temuan utama |
|---|---|---|
| [01 Eksplorasi Listing](notebooks/01_eksplorasi_listing.ipynb) | Pembersihan data, harga, geografi, diskon, kata kunci nama produk | "Premium" dipakai produk di bawah harga median; rating berkorelasi *negatif* dengan penjualan |
| [02 Analisis Ulasan](notebooks/02_analisis_ulasan.ipynb) | Tema pujian vs keluhan | Kesesuaian deskripsi paling sering dipuji sekaligus dikeluhkan; harga hampir tidak pernah dipuji |
| [03 Model Ulasan](notebooks/03_model_ulasan.ipynb) | Sentimen, prediksi rating, klasifikasi kategori | Model menangkap keluhan yang luput dari aturan; pemisahan acak menaikkan skor secara semu |
| [04 Uji Sensitivitas Skor](notebooks/04_uji_sensitivitas_skor.ipynb) | Variasi desain, ablasi, bootstrap | Hanya dua segmen teratas yang kokoh; skor menunjuk pasar sepi, belum tentu pasar besar |

## Machine learning

Semua model adalah baseline yang dievaluasi dengan jujur: TF-IDF + regresi
logistik, dengan data latih dan uji **dipisah per produk**, dan setiap model
dibandingkan dengan tebakan paling sederhana.

| Tugas | Hasil | Pembanding | Pelajaran |
|---|---|---|---|
| Sentimen negatif | F1 48,2% (recall 80,4%, precision 34,5%) | "Selalu bukan negatif": akurasi 96,8%, F1 0% | Akurasi menyesatkan untuk data tidak seimbang (keluhan hanya 2,3%) |
| Rating 1-5 | Macro-F1 0,386 | "Selalu bintang 5": macro-F1 0,167, tapi MAE-nya lebih baik (0,422 vs 0,519) | Tidak ada model terbaik mutlak; metrik dipilih dari kebutuhan sebelum melatih |
| Kategori dari teks ulasan | Akurasi 44,7% | "Selalu kategori terbanyak": 36,8% | Ulasan Tokopedia lebih banyak menilai transaksi daripada barangnya |

**Model mendeteksi, aturan menjelaskan.** Model sentimen dipakai di tab Cek
Ulasan karena lebih jeli: ia menangkap ejaan gaul (`"tdk bs dipakai"`) dan
kalimat tidak langsung (`"beli 3, cuma 1 yang bisa dipakai"`) yang tidak pernah
didaftarkan. Tapi lapis Diagnostik tetap memakai aturan kata kunci, karena
angkanya harus bisa ditelusuri ke kata pemicunya. Grafik kontribusi kata di
tab Cek Ulasan juga bukan perkiraan: untuk regresi logistik, jumlah kontribusi
itu persis nilai yang dihitung model, dan kesamaan ini diuji otomatis.

**Sengaja tidak dikerjakan:** sistem rekomendasi (dataset tidak memuat identitas
pengulas, jadi collaborative filtering tidak mungkin), dan melatih language
model sendiri (40 ribu ulasan pendek terlalu sedikit). Langkah lanjut yang
realistis adalah fine-tuning IndoBERT.

## Skor peluang

Skor ini dirancang sendiri, menggabungkan tiga sinyal dalam satuan z-score:

```
skor_peluang = nilai_penjualan − jumlah_pesaing + porsi_pesaing_lemah
```

Logikanya: sebuah segmen menarik kalau uang yang berputar besar, pesaingnya
sedikit, dan cukup banyak pesaing yang mengecewakan pembeli.

### Versi pertama gagal

| Versi pertama | Masalah | Versi sekarang |
|---|---|---|
| Permintaan dalam unit terjual | Segmen termurah selalu menang, karena obeng Rp14 ribu pasti laku lebih banyak dari bor Rp2 juta | Nilai penjualan dalam Rupiah |
| Kepuasan = rating median | Rating Tokopedia menggelembung: median hampir semua segmen 4,9-5,0, selisihnya noise | Porsi pesaing dengan rating di bawah 4,7 |
| Rating 0 dihitung apa adanya | Rating 0 berarti belum dinilai, bukan dinilai terburuk | Rating 0 dianggap kosong |

### Seberapa kokoh peringkatnya?

Skor ini tidak punya kunci jawaban, jadi tidak bisa divalidasi seperti model.
Yang bisa diuji adalah apakah peringkatnya bertahan ketika asumsinya diubah
([notebook 04](notebooks/04_uji_sensitivitas_skor.ipynb)):

- **Pilihan desain:** ambang, bobot tiap komponen, transformasi log, dan
  persentil pemangkasan diubah satu per satu (13 variasi). Peringkat 1 tidak
  pernah berubah. Persentil pemangkasan hampir tidak berpengaruh (korelasi
  peringkat ≥0,99), dan bobot adalah asumsi paling sensitif.
- **Kebetulan sampel:** produk diambil ulang 300 kali dengan pengembalian, lalu
  seluruh proses diulang. Otomotif Menengah dan Super Premium bertahan di 5
  besar pada 95% dan 87% sampel ulang. Segmen di peringkat 4-10 umumnya bertahan
  di bawah 40%, jadi urutannya praktis tidak bisa dibedakan. Dashboard
  menampilkan angka ini di samping setiap segmen.
- **Ablasi:** membuang komponen pesaing lemah atau jumlah pesaing mengubah papan
  atas hampir seluruhnya, sedangkan membuang nilai penjualan mengubah paling
  sedikit. Temuan ini diungkapkan apa adanya, bukan ditutupi dengan mengatur
  ulang bobot sampai hasilnya terlihat masuk akal.

Batasnya: bootstrap mengukur *variasi* sampel, bukan *bias*-nya. Kokoh tidak
sama dengan benar.

## Tantangan data yang diselesaikan

1. **Kategori harus diturunkan dari nama produk.** Versi awal memakai pencocokan
   potongan huruf, sehingga `"mur"` (pertukangan) ikut cocok dengan `"murah"` dan
   `"tang"` dengan "Manset `Tang`an". Bug ini membuat kategori pertukangan
   menggelembung dari 440 menjadi 1.469 produk, dan total 2.789 produk (9,5%)
   salah kategori, tanpa satu pun pesan error. Pencocokan kata utuh membuat
   produk tak terklasifikasi naik, dan trade-off itu disengaja: produk yang salah
   kategori merusak analisis, sedangkan yang tak terkategori hanya tidak ikut
   dihitung. Taksonomi diperluas dari 5 ke 12 kategori; porsi tak terklasifikasi
   akhirnya 25%.

2. **Satu listing menguasai 51% total nilai pasar.** Mobil seharga Rp900 juta
   berlabel "9rb+ terjual", hampir pasti listing uang muka atau data salah.
   Diatasi dengan *winsorizing* per kategori di persentil 99,5: outlier tidak
   dibuang, hanya dipangkas. Porsi 10 produk teratas terhadap total nilai pasar
   turun dari 61,9% menjadi 4,6%.

3. **Kolom angka berupa teks** seperti `"1rb+ terjual"`, `"1,2rb+ terjual"`, dan
   `"10 ulasan"`. Dikonversi dengan kesadaran bahwa hasilnya batas bawah.

4. **Lokasi tidak konsisten.** Ada belasan variasi Jakarta (`"Dki Jakarta"`,
   `"Pancoran, Kota Jakarta Selatan"`), plus 2.820 toko berlokasi `"Indonesia"`
   yang bukan nama kota.

5. **Kata kunci keluhan disusun dari data, bukan tebakan.** Ulasan negatif yang
   lolos dibaca manual, lalu ditambahkan ejaan gaul (`"tdk sesuai"`, `"blm
   sampe"`) dan tema yang terlewat. Kata yang juga muncul dalam pujian, seperti
   `"gambar"` pada "sesuai gambar", sengaja tidak dipakai sendirian.

6. **Kedua dataset tidak bisa digabung per produk**, karena tidak ada kunci yang
   sama dan periodenya berbeda. Jembatannya adalah normalisasi kategori, sehingga
   perbandingan hanya dilakukan pada level yang memang sah.

## Etika pengumpulan data

Komponen scraping (`src/scrape_sample.py`) memeriksa `robots.txt` lebih dulu dan
berhenti bila aksesnya dilarang. Hasil pemeriksaan dicatat sebagai temuan, bukan
rintangan yang diakali.

## Sumber data dan lisensi

`database.db` berisi hasil olahan kedua dataset berikut, disebarkan ulang
sesuai lisensinya masing-masing:

| Dataset | Pembuat di Kaggle | Lisensi |
|---|---|---|
| [Indonesia E-Commerce Dataset: Tokopedia Listings](https://www.kaggle.com/datasets/pandaa12/indonesia-e-commerce-dataset-tokopedia-listings) | pandaa12 | Apache 2.0 |
| [Tokopedia Product Reviews](https://www.kaggle.com/datasets/farhan999/tokopedia-product-reviews) | farhan999 | MIT |

## Stack

Python · pandas · SQLite · scikit-learn · SciPy · Sastrawi (stemming Bahasa
Indonesia) · Streamlit · Plotly · pytest

## Cara menjalankan

**1. Siapkan environment**

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**2. Unduh data**

Data mentah tidak ikut di-commit. Yang ikut hanya `database.db` hasil olahan,
supaya dashboard bisa dibuka tanpa menjalankan pipeline. Untuk menjalankan
pipeline sendiri, unduh kedua dataset dari Kaggle dan taruh di `data/raw/`:

| Dataset | Nama file yang diharapkan |
|---|---|
| [Indonesia E-Commerce Dataset: Tokopedia Listings](https://www.kaggle.com/datasets/pandaa12/indonesia-e-commerce-dataset-tokopedia-listings) | `produk_tokopedia.csv` |
| [Tokopedia Product Reviews](https://www.kaggle.com/datasets/farhan999/tokopedia-product-reviews) | `tokopedia-product-reviews-2019.csv` |

**3. Jalankan pipeline**

```bash
python run_pipeline.py
```

Pipeline membersihkan data, menghitung skor peluang beserta uji kestabilannya,
menganalisis ulasan, melatih model sentimen, lalu memuat semuanya ke SQLite.

**4. Buka dashboard**

```bash
streamlit run app.py
```

**5. Jalankan test**

Test memakai data sintetis kecil, jadi bisa dijalankan tanpa mengunduh dataset.

```bash
pip install -r requirements-dev.txt
pytest
```

**6. (Opsional) Jalankan ulang notebook**

Hasil notebook sudah tersimpan dan bisa dibaca langsung di GitHub. Untuk
menjalankannya sendiri:

```bash
pip install jupyter
jupyter lab notebooks/
```

## Struktur project

```
├── data/
│   ├── raw/                  data asli, tidak pernah diubah (tidak di-commit)
│   └── processed/            hasil cleaning (dibuat pipeline, tidak di-commit)
├── database.db               hasil akhir pipeline, dibaca dashboard
├── models/                   model sentimen dan metrik evaluasinya
├── src/
│   ├── config.py             path, taksonomi kategori, tema keluhan
│   ├── clean_listings.py     parsing harga & terjual, kategorisasi, pemangkasan outlier
│   ├── clean_reviews.py      pembersihan ulasan
│   ├── opportunity.py        segmentasi harga & skor peluang
│   ├── sensitivity.py        uji kestabilan skor peluang (variasi desain & bootstrap)
│   ├── review_analysis.py    tema keluhan & TF-IDF
│   ├── sentiment_model.py    pelatihan, evaluasi, dan penjelasan model sentimen
│   ├── scrape_sample.py      scraping dengan pengecekan robots.txt
│   ├── build_db.py           pemuatan ke SQLite
│   └── plot_style.py         gaya grafik notebook, satu palet dengan dashboard
├── notebooks/                empat notebook analisis (01-04)
├── tests/                    test otomatis, memakai data sintetis
├── run_pipeline.py           orkestrasi seluruh proses
└── app.py                    dashboard Streamlit
```

Pemisahan `raw` dan `processed` disengaja: data mentah tidak pernah disentuh,
sehingga seluruh proses bisa diulang dari nol kapan pun.

## Keterbatasan

- **Jumlah pesaing diukur dari sampel scraping, bukan seluruh Tokopedia.**
  Skor peluang teratas didominasi otomotif (390 produk), yang bisa jadi tampak
  sepi pesaing hanya karena jarang ter-scrape. Uji bootstrap tidak bisa
  mendeteksi bias seperti ini.
- **Skor peluang menunjuk pasar yang sepi dan kurang terlayani, belum tentu
  pasar yang besar.** Sebagian besar segmen teratas bernilai penjualan di bawah
  rata-rata.
- **Model sentimen banyak memberi peringatan palsu**: dua dari tiga ulasan yang
  ditandai keluhan sebenarnya bukan keluhan. Ini harga dari recall 80% pada data
  yang keluhannya hanya sekitar 3%. Model dilatih dari ulasan 2019 di lima
  kategori saja.
- **Rating menggelembung**: hanya 2,3% ulasan berbintang 1-2, sehingga lapis
  diagnostik bertumpu pada sekitar 900 ulasan. Kategori pertukangan hanya punya
  24 ulasan negatif.
- Sekitar 31% ulasan negatif tidak tertangkap tema apa pun: campuran kekecewaan
  umum, pujian dengan bintang rendah, dan keluhan yang luput karena ejaan gaul
  atau kalimat tidak langsung.
- Perkiraan nilai pasar adalah **batas bawah** karena keterbatasan kolom terjual.
- Ulasan hanya mencakup lima kategori, jadi lapis diagnostik tidak tersedia
  untuk kategori lain.
- Data adalah potret satu waktu, bukan deret waktu, sehingga tren musiman tidak
  bisa dianalisis.
- Dataset ulasan berasal dari 2019, lebih lama dari dataset listing. Perbandingan
  antar keduanya hanya sah pada level pola kategori, bukan angka absolut.
