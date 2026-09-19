import math

import pandas as pd
import pytest

from src import clean_listings as cl


@pytest.mark.parametrize("teks, hasil", [
    ("1rb+ terjual", 1_000),
    ("1,2rb+ terjual", 1_200),
    ("250+ terjual", 250),
    ("2jt+ terjual", 2_000_000),
    ("10 ulasan", 10),
    ("", 0),
    (None, 0),
])
def test_parse_terjual(teks, hasil):
    assert cl.parse_terjual(teks) == hasil


@pytest.mark.parametrize("teks, hasil", [
    ("Rp1.234.567", 1_234_567),  # titik adalah pemisah ribuan, bukan desimal
    ("Rp 15.000", 15_000),
    (15000, 15_000),
])
def test_parse_harga(teks, hasil):
    assert cl.parse_harga(teks) == hasil


def test_parse_harga_kosong_jadi_nan():
    assert math.isnan(cl.parse_harga(None))


# Regresi untuk bug yang dulu membuat 9,5% produk salah kategori tanpa error:
# pencocokan potongan huruf membuat "mur" cocok dengan "murah" dan "tang"
# cocok dengan "tangan".
@pytest.mark.parametrize("nama", [
    "Kaos Polos Murah Cotton Combed",
    "Manset Tangan Pria Anti UV",
    "Sarung Tangan Motor",
])
def test_kata_pendek_tidak_cocok_di_dalam_kata_lain(nama):
    assert cl.tentukan_kategori(nama) != "pertukangan"


@pytest.mark.parametrize("nama, kategori", [
    ("Obeng Set 6 in 1", "pertukangan"),
    ("Mur Baut M8 Stainless", "pertukangan"),
    ("Jam Tangan Pria Digital", "fashion"),
    # Frasa spesifik harus menang atas kata umum: "sepatu bola" vs "sepatu".
    ("Sepatu Bola Anak Size 30", "olahraga"),
    ("Sepatu Sneakers Wanita", "fashion"),
])
def test_tentukan_kategori(nama, kategori):
    assert cl.tentukan_kategori(nama) == kategori


def test_nama_tanpa_kata_kunci_masuk_lainnya():
    assert cl.tentukan_kategori("Voucher Game 100 Diamond") == "lainnya"
    assert cl.tentukan_kategori(None) == "lainnya"


@pytest.mark.parametrize("lokasi, hasil", [
    ("Kota Jakarta Barat", "Jakarta Barat"),
    ("Pancoran, Kota Jakarta Selatan", "Jakarta Selatan"),
    ("Jakarta Barat, Dki Jakarta", "Jakarta Barat"),
    ("Dki Jakarta", "Jakarta"),
    ("KABUPATEN BANDUNG", "Bandung"),
    ("Indonesia", "Tidak Diketahui"),  # bukan nama kota
    (None, "Tidak Diketahui"),
])
def test_normalisasi_lokasi(lokasi, hasil):
    assert cl.normalisasi_lokasi(lokasi) == hasil


def test_semua_kota_jakarta_digabung():
    for kota in ["Jakarta", "Jakarta Barat", "Jakarta Selatan"]:
        assert cl.tentukan_wilayah(kota) == "DKI Jakarta"
    assert cl.tentukan_wilayah("Bandung") == "Bandung"


def test_pemangkasan_membatasi_outlier_tanpa_membuang_baris():
    # Tiruan kasus mobil Rp900 juta berlabel "9rb+ terjual".
    df = pd.DataFrame({
        "kategori": ["otomotif"] * 1000 + ["fashion"] * 1000,
        "estimasi_omzet_mentah": list(range(1, 1000)) + [8.1e12] + list(range(1, 1001)),
    })
    hasil = cl.pangkas_per_kategori(df)

    assert len(hasil) == len(df)
    assert hasil.iloc[999] < 1_000  # outlier dipangkas ke persentil 99,5 kategorinya
    assert (hasil.iloc[:995] == df["estimasi_omzet_mentah"].iloc[:995]).all()  # sisanya utuh


def test_pemangkasan_dihitung_per_kategori():
    # Outlier di satu kategori tidak boleh menggeser batas kategori lain.
    df = pd.DataFrame({
        "kategori": ["otomotif"] * 200 + ["fashion"] * 200,
        "estimasi_omzet_mentah": [1e12] * 200 + list(range(1, 201)),
    })
    hasil = cl.pangkas_per_kategori(df)
    assert hasil[df["kategori"] == "fashion"].max() < 201
