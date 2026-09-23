import math

import pandas as pd
import pytest

from src.produk import bersihkan_produk, rapikan_lokasi, tentukan_kategori, ubah_ke_angka


def kosong(x):
    return x is None or (isinstance(x, float) and math.isnan(x))


# Contoh-contoh ini berasal dari temuan di notebook 01 dan 02
@pytest.mark.parametrize("teks, kata, harapan", [
    ("26 terjual", "terjual", 26),
    ("100+ terjual", "terjual", 100),
    ("1rb+ terjual", "terjual", 1_000),
    ("4 rb+ Terjual", "terjual", 4_000),
    ("4.95rb+ terjual", "terjual", 4_950),
    ("1jt+ terjual", "terjual", 1_000_000),
    ("223 sold", "terjual|sold", 223),
    ("1.000 ulasan", "ulasan", 1_000),
    ("7.426 ulasan", "ulasan", 7_426),
    ("1.2rb ulasan", "ulasan", 1_200),
    ("1,3 rb ulasan", "ulasan", 1_300),
    ("1.5K ulasan", "ulasan", 1_500),
])
def test_ubah_ke_angka(teks, kata, harapan):
    assert ubah_ke_angka(teks, kata) == harapan


@pytest.mark.parametrize("teks, kata", [
    ("150 stok", "terjual"),
    ("103 rating", "terjual"),
    ("Best Seller", "terjual"),
    ("1,6 rb ulasan toko", "ulasan"),
    ("Tidak tersedia", "ulasan"),
    (None, "terjual"),
])
def test_ubah_ke_angka_bukan_jumlah(teks, kata):
    assert kosong(ubah_ke_angka(teks, kata))


@pytest.mark.parametrize("teks, harapan", [
    ("Kota Administrasi Jakarta Barat", "Jakarta"),
    ("Jakarta Selatan", "Jakarta"),
    ("Kab. Bandung", "Bandung"),
    ("Kota Bandung", "Bandung"),
    ("Bekasi, Jawa Barat", "Bekasi"),
    ("Surabaya", "Surabaya"),
])
def test_rapikan_lokasi(teks, harapan):
    assert rapikan_lokasi(teks) == harapan


def test_rapikan_lokasi_kosong():
    assert kosong(rapikan_lokasi(None))


@pytest.mark.parametrize("nama, harapan", [
    ("Raw Food Beef / Dog Food 1KG", "Hewan Peliharaan"),
    ("Kaos Polos Pria Cotton Combed", "Fashion"),
    ("Mouse Gaming Wireless RGB", "Elektronik"),
    ("Kabel Data Type C Fast Charging", "Handphone"),
    ("Jam Tangan Kualitas Premium", "Fashion"),
    ("Barang Unik Tanpa Kata Kunci", "Lainnya"),
])
def test_tentukan_kategori(nama, harapan):
    assert tentukan_kategori(nama) == harapan


# Kasus yang dulu salah golong. Contoh diambil dari nama produk asli di data.
@pytest.mark.parametrize("nama, harapan", [
    ("Mainan Anak Mobil Sedan Plastik Mobilan Murah Toys", "Ibu, Bayi & Mainan"),   # dulu Otomotif
    ("Car Charger Mobil 60W PD USB-C USB-A Super Fast Charging", "Handphone"),        # dulu Otomotif
    ("Tas Laptop Macbook Softcase Sleeve Nylon Waterproof", "Elektronik"),           # dulu Handphone
    ("Alexandre Christie Wanita AC 2976 BH Original", "Fashion"),                    # dulu Elektronik
    ("Toples Jar Toples Plastik PET 800ml", "Rumah Tangga"),                         # dulu Hewan Peliharaan
    ("Helm Bogo Classic SNI Dewasa Helm Pet", "Otomotif"),                           # dulu Hewan Peliharaan
    ("Car Charger Samsung USB-C 1 Port 25W RC-01", "Handphone"),                     # "RC-01" bukan mainan RC
    ("AC SPLIT SHARP 1.5 PK AH-A12SAY R32", "Elektronik"),                           # AC sungguhan tetap Elektronik
    ("Gelang casteli dua mainan emas tua kadar 16k", "Perhiasan"),                   # "mainan" di sini istilah perhiasan
    ("Napolly Rak Sepatu Susun Muat 20 Pasang", "Rumah Tangga"),                     # dulu Fashion
    ("Dunlopillo Sarung Bantal Pincore 65x45", "Rumah Tangga"),                      # dulu Fashion
    ("Rexus RGC R60 Gaming Chair with Footrest", "Rumah Tangga"),                    # dulu Elektronik
    ("ecentio tumbler Stainless Vacuum 900ml", "Rumah Tangga"),                      # dulu Elektronik
    ("Xiaomi Redmi Watch 5 Active Smartwatch 2.0 LCD", "Elektronik"),                 # smartwatch bukan Fashion
    ("JAM TANGAN LARI DIGITAL HITAM LED SPORTY", "Fashion"),                         # dulu Elektronik
    ("New DEERMA CM800 VACUUM CLEANER UV-C ANTI DEBU TUNGAU KASUR", "Elektronik"),    # "kasur" tidak menang
    ("Mainan Anak Tumbler Up Side Down Roly Poly", "Ibu, Bayi & Mainan"),            # "tumbler" tidak menang
    ("makanan ikan terbaik/pelet ikan SAKURA", "Hewan Peliharaan"),                  # dulu Makanan & Minuman
    ("Salsa Galaxy Eyeshadow Palette 3 Varian Warna", "Kesehatan & Kecantikan"),     # dulu Handphone
    ("ORI Charger Laptop Lenovo Ideapad 100 110", "Elektronik"),                     # dulu Handphone
])
def test_kategori_kasus_ambigu(nama, harapan):
    assert tentukan_kategori(nama) == harapan


def test_kata_kunci_harus_kata_utuh():
    # "tas" tidak boleh cocok dengan "kualitas"
    assert tentukan_kategori("Kualitas Terbaik Nomor Satu") == "Lainnya"


def test_bersihkan_produk_contoh_kecil():
    mentah = pd.DataFrame({
        "Nama Produk": ["Kaos Polos", "Kaos Polos", "Mouse Gaming", "Sapu Lantai"],
        "Nama Toko": ["A", "A", "B", "C"],
        "Lokasi Toko": ["Jakarta Barat", "Jakarta Barat", "Kab. Bandung", "Indonesia"],
        "Terjual": ["1rb+ terjual", "1rb+ terjual", "Best Seller", "5 terjual"],
        "Jumlah Ulasan": ["10 ulasan", "10 ulasan", None, "1.2rb ulasan"],
        "Rating": [4.9, 4.9, 0.0, 5.0],
        "Harga (IDR)": [50_000, 50_000, 150_000, 0],
        "Diskon (%)": [0.0, 0.0, 10.0, 0.0],
        "Produk URL": ["u1", "u1", "u2", "u3"],
    })
    referensi = pd.DataFrame({
        "lokasi": ["Jakarta", "Bandung"],
        "kota": ["Jakarta", "Bandung"],
        "provinsi": ["DKI Jakarta", "Jawa Barat"],
    })

    bersih, jejak = bersihkan_produk(mentah, referensi)

    # Satu duplikat dan satu produk berharga 0 dibuang
    assert jejak == {"Data awal": 4, "Setelah buang duplikat": 3, "Setelah buang harga 0": 2, "Data bersih": 2}
    assert bersih["terjual"].tolist()[0] == 1_000
    assert pd.isna(bersih["terjual"].tolist()[1])
    # Rating 0 berarti belum dinilai, jadi dijadikan kosong
    assert pd.isna(bersih["rating"].iloc[1])
    assert bersih["provinsi"].tolist() == ["DKI Jakarta", "Jawa Barat"]
    assert bersih["kategori"].tolist() == ["Fashion", "Elektronik"]
