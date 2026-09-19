import pandas as pd
import pytest

from src.teks import bersihkan_teks
from src.ulasan import bersihkan_ulasan


# Contoh-contoh ini berasal dari temuan di notebook 04 dan 05
@pytest.mark.parametrize("teks, harapan", [
    ("Goood banget gan!!!", "good banget gan"),
    ("Terima kasih, barang udah sampe &amp; rapih", "terimakasih barang sudah sampai rapi"),
    ("Brg gk sesuai, kecewaaa 😡", "barang tidak sesuai kecewa"),
    ("Barang tdk berfungsi, sdh chat seller tp gk dibales",
     "barang tidak berfungsi sudah chat seller tapi tidak dibales"),
    ("gara&#34; salah kurir", "gara salah kurir"),
    ("Pengiriman 2 hari, cepet!", "pengiriman hari cepat"),
    ("👍👍👍", ""),
    ("......", ""),
])
def test_bersihkan_teks(teks, harapan):
    assert bersihkan_teks(teks) == harapan


def test_semua_varian_tidak_menjadi_tidak():
    for varian in ["ga", "gak", "gk", "tdk", "ngga", "nggak", "engga", "enggak"]:
        assert bersihkan_teks(f"barang {varian} bagus") == "barang tidak bagus"


def test_bersihkan_ulasan_contoh_kecil():
    mentah = pd.DataFrame({
        "Unnamed: 0": [1, 2, 3, 4, 5],
        "text": ["Barang bagus", "Barang bagus", "Kecewa brg rusak", "Biasa aja", "👍👍👍"],
        "rating": [5, 5, 1, 3, 5],
        "category": ["fashion"] * 5,
        "product_name": ["Kaos &#40;Polos&#41;"] * 5,
        "product_id": [10, 10, 10, 10, 11],
        "sold": ["1"] * 5,
        "shop_id": [1] * 5,
        "product_url": ["u"] * 5,
    })

    bersih, jejak = bersihkan_ulasan(mentah)

    # Duplikat di produk yang sama, bintang 3, dan teks yang kosong setelah dibersihkan dibuang
    assert jejak["Setelah buang duplikat"] == 4
    assert jejak["Setelah buang bintang 3"] == 3
    assert jejak["Data bersih"] == 2
    assert bersih["label"].tolist() == ["positif", "negatif"]
    assert bersih["teks_bersih"].tolist() == ["barang bagus", "kecewa barang rusak"]
    assert bersih["nama_produk"].iloc[0] == "Kaos (Polos)"
