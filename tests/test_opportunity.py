import numpy as np
import pandas as pd
import pytest

from src import opportunity as op


def test_z_score_aman_saat_semua_nilai_sama():
    assert (op._z(pd.Series([3.0, 3.0, 3.0])) == 0).all()


def test_segmen_harga_dihitung_per_kategori():
    # Harga Rp2 juta itu murah untuk handphone tapi mahal untuk obeng.
    df = pd.DataFrame({
        "kategori": ["pertukangan"] * 4 + ["handphone"] * 4,
        "harga": [10_000, 50_000, 200_000, 2_000_000,
                  2_000_000, 4_000_000, 8_000_000, 16_000_000],
    })
    segmen = op.beri_segmen_harga(df)["segmen_harga"]
    assert segmen.iloc[3] == "Super Premium"  # obeng Rp2 juta
    assert segmen.iloc[4] == "Ekonomis"  # handphone Rp2 juta


def test_segmen_harga_untuk_satu_kategori_saja():
    # Regresi: dengan satu kategori yang harganya tidak bisa dibagi empat,
    # groupby().apply() dulu menghasilkan tabel melebar dan fungsinya crash.
    df = pd.DataFrame({"kategori": ["olahraga"] * 4, "harga": [10_000] * 4})
    assert (op.beri_segmen_harga(df)["segmen_harga"] == "Menengah").all()


def test_kategori_lainnya_tidak_ikut_dinilai(listings_sintetis):
    df = pd.concat([listings_sintetis, listings_sintetis.head(10).assign(kategori="lainnya")])
    assert "lainnya" not in set(op.agregasi_segmen(df)["kategori"])


def test_porsi_pesaing_lemah_mengabaikan_produk_tanpa_rating():
    # Rating kosong berarti belum dinilai. Dari dua produk berating, satu di
    # bawah 4,7, jadi porsinya 50%, bukan 25%.
    df = pd.DataFrame({
        "kategori": ["olahraga"] * 4, "nama_produk": list("abcd"), "nama_toko": list("abcd"),
        "harga": [10_000] * 4, "terjual": [1.0] * 4, "estimasi_omzet": [10_000.0] * 4,
        "rating": [4.5, 5.0, np.nan, np.nan], "diskon": [0.0] * 4,
    })
    assert op.agregasi_segmen(df)["porsi_pesaing_lemah"].iloc[0] == pytest.approx(0.5)


def test_rumus_skor_peluang(listings_sintetis):
    hasil = op.beri_skor(op.agregasi_segmen(listings_sintetis))
    harapan = hasil["skor_permintaan"] - hasil["skor_kompetisi"] + hasil["skor_pesaing_lemah"]

    assert np.allclose(hasil["skor_peluang"], harapan, atol=0.002)  # toleransi pembulatan 3 desimal
    assert hasil["skor_peluang"].is_monotonic_decreasing


def test_bobot_nol_membuang_komponen(listings_sintetis):
    hasil = op.beri_skor(op.agregasi_segmen(listings_sintetis), bobot=(1, 1, 0))
    harapan = hasil["skor_permintaan"] - hasil["skor_kompetisi"]
    assert np.allclose(hasil["skor_peluang"], harapan, atol=0.002)
