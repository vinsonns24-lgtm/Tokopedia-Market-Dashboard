import numpy as np
import pandas as pd
import pytest

from src import sentiment_model as sm


@pytest.fixture
def ulasan_sintetis() -> pd.DataFrame:
    # Beberapa produk punya banyak ulasan, seperti data aslinya.
    negatif = ["barang rusak kecewa", "tidak sesuai pesanan", "jelek banget kecewa",
               "rusak tidak bisa dipakai"]
    positif = ["barang bagus mantap", "pengiriman cepat mantap", "sesuai pesanan bagus",
               "bagus sekali terima kasih"]
    baris = []
    for produk in range(30):
        for i in range(1 + produk % 5):
            neg = (produk + i) % 4 == 0
            teks = (negatif if neg else positif)[(produk + i) % 4]
            baris.append({"ulasan": teks, "is_negatif": neg, "produk_id": f"p{produk}"})
    return pd.DataFrame(baris)


def test_pemisahan_tidak_membocorkan_produk(ulasan_sintetis):
    idx_latih, idx_uji = sm.pisah_per_produk(ulasan_sintetis)
    produk_latih = set(ulasan_sintetis["produk_id"].iloc[idx_latih])
    produk_uji = set(ulasan_sintetis["produk_id"].iloc[idx_uji])

    assert produk_latih.isdisjoint(produk_uji)
    assert len(idx_latih) + len(idx_uji) == len(ulasan_sintetis)


def test_penjelasan_sama_persis_dengan_hitungan_model(ulasan_sintetis):
    # Dashboard mengklaim grafik kontribusi kata "bukan perkiraan". Klaim itu
    # benar hanya kalau jumlah semua kontribusi + intersep = skor model.
    model = sm.buat_model().fit(ulasan_sintetis["ulasan"], ulasan_sintetis["is_negatif"])
    nama_fitur = model.named_steps["tfidf"].get_feature_names_out()
    teks = "barang rusak dan tidak sesuai"

    proba, kontribusi = sm.jelaskan(model, teks, nama_fitur, top_n=10_000)
    intersep = model.named_steps["logreg"].intercept_[0]

    assert kontribusi["kontribusi"].sum() + intersep == pytest.approx(model.decision_function([teks])[0])
    assert proba == pytest.approx(model.predict_proba([teks])[0, 1])


def test_kontribusi_diurutkan_dari_yang_paling_berpengaruh(ulasan_sintetis):
    model = sm.buat_model().fit(ulasan_sintetis["ulasan"], ulasan_sintetis["is_negatif"])
    nama_fitur = model.named_steps["tfidf"].get_feature_names_out()

    _, kontribusi = sm.jelaskan(model, "barang rusak kecewa tapi pengiriman cepat", nama_fitur, top_n=3)

    assert len(kontribusi) == 3
    assert np.all(np.diff(kontribusi["kontribusi"].abs()) <= 0)
