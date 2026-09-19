import pandas as pd
import pytest

from src import review_analysis as ra


@pytest.mark.parametrize("ulasan, tema", [
    ("pengiriman lama banget", "Pengiriman"),
    ("barangnya rusaknya parah", "Kualitas Produk"),  # akhiran "-nya" tetap cocok
    ("tdk sesuai gambar", "Tidak Sesuai Deskripsi"),  # ejaan gaul
    ("barang tidak bisa nyala sama sekali", "Tidak Berfungsi"),
    ("ini barang KW bukan ori", "Keaslian"),
])
def test_tema_terdeteksi(ulasan, tema):
    assert tema in ra.tandai_tema(ulasan)


# Regresi: pencocokan potongan huruf sempat membuat "mati" cocok dengan
# "otomatis" dan "kw" cocok dengan "kwalitas".
@pytest.mark.parametrize("ulasan, tema", [
    ("lampu otomatis menyala, mantap", "Tidak Berfungsi"),
    ("kwalitas bagus sesuai harga", "Keaslian"),
])
def test_kata_pendek_tidak_cocok_di_dalam_kata_lain(ulasan, tema):
    assert tema not in ra.tandai_tema(ulasan)


def test_pujian_tidak_dianggap_keluhan():
    # "gambar" sengaja tidak dijadikan kata kunci karena muncul di pujian.
    assert ra.tandai_tema("barang sesuai gambar, terima kasih") == []


def test_satu_ulasan_bisa_punya_beberapa_tema():
    tema = ra.tandai_tema("pengiriman lama dan kemasan penyok")
    assert {"Pengiriman", "Kemasan"} <= set(tema)


def test_porsi_tema_dihitung_dari_jumlah_ulasan_negatif():
    reviews = pd.DataFrame({
        "kategori": ["fashion"] * 6,
        "ulasan": [
            "pengiriman lama", "pengiriman telat", "barang jelek", "kecewa",
            "pengiriman lama sekali",  # positif: tidak boleh ikut dihitung
            "mantap",
        ],
        "is_negatif": [True, True, True, True, False, False],
    })
    hasil = ra.hitung_tema_keluhan(reviews).set_index("tema")

    assert hasil.loc["Pengiriman", "jumlah"] == 2
    assert hasil.loc["Pengiriman", "porsi"] == pytest.approx(2 / 4)
