"""Lapisan breakdown: mencari celah pasar per kategori dan segmen harga.

Logika skor peluang: sebuah segmen menarik kalau uang yang berputar besar,
pesaingnya sedikit, dan cukup banyak pesaing yang mengecewakan pembeli.
Yang terakhir penting — pesaing yang semuanya dinilai bagus sulit digeser,
sedangkan pesaing lemah berarti ada ruang masuk dengan produk yang lebih baik.

Dua pilihan desain yang disengaja:
- Permintaan diukur dalam Rupiah, bukan unit. Dengan unit, segmen termurah
  selalu menang karena barang murah laku lebih banyak — padahal penjual
  peduli pada uang yang masuk.
- Kepuasan diukur sebagai porsi pesaing dengan rating di bawah ambang, bukan
  rating median. Rating Tokopedia sangat menggelembung (median 5,0), sehingga
  selisih median antar segmen hanya 0,1 dan praktis tidak bermakna.
"""

import numpy as np
import pandas as pd

from .config import DATA_PROCESSED

LABEL_SEGMEN = ["Ekonomis", "Menengah", "Premium", "Super Premium"]

# Kuartil bawah rating listing adalah 4,8, jadi di bawah 4,7 sudah jelas di
# bawah kebiasaan pasar.
AMBANG_PESAING_LEMAH = 4.7


def _z(series: pd.Series) -> pd.Series:
    """Z-score yang aman terhadap deviasi nol."""
    std = series.std()
    if not std or np.isnan(std):
        return pd.Series(0.0, index=series.index)
    return (series - series.mean()) / std


def beri_segmen_harga(listings: pd.DataFrame) -> pd.DataFrame:
    """Bagi harga jadi empat segmen berdasarkan kuartil *dalam* tiap kategori.

    Kuartil per kategori, bukan global, karena rentang harga antar kategori
    sangat berbeda. Handphone Rp2 juta itu kelas menengah, sedangkan obeng
    Rp2 juta jelas bukan.
    """
    df = listings.copy()

    def _segmen(grup: pd.DataFrame) -> pd.Series:
        try:
            return pd.qcut(grup["harga"], q=4, labels=LABEL_SEGMEN, duplicates="drop")
        except ValueError:
            # Terjadi kalau variasi harga terlalu sedikit untuk dibagi empat.
            return pd.Series("Menengah", index=grup.index)

    # Digabung manual, bukan lewat groupby().apply(): kalau hanya ada satu
    # kategori, apply() menyusun hasilnya jadi tabel melebar dan penugasan gagal.
    bagian = [_segmen(grup) for _, grup in df.groupby("kategori")]
    df["segmen_harga"] = pd.concat(bagian).astype(str) if bagian else pd.Series(dtype=str)
    return df


def agregasi_segmen(
    listings: pd.DataFrame,
    ambang: float = AMBANG_PESAING_LEMAH,
    kolom_omzet: str = "estimasi_omzet",
) -> pd.DataFrame:
    """Ringkas tiap kombinasi kategori x segmen harga, sebelum diberi skor.

    Ambang dan kolom omzet bisa diganti supaya uji sensitivitas (notebook 04)
    memakai kode yang sama persis dengan dashboard.
    """
    # "lainnya" adalah campuran produk tak sejenis; skor peluangnya tidak punya
    # makna bisnis dan hanya akan menggeser z-score kategori lain.
    df = beri_segmen_harga(listings[listings["kategori"] != "lainnya"])

    ringkasan = (
        df.groupby(["kategori", "segmen_harga"])
        .agg(
            jumlah_produk=("nama_produk", "count"),
            jumlah_penjual=("nama_toko", "nunique"),
            median_harga=("harga", "median"),
            total_terjual=("terjual", "sum"),
            median_terjual=("terjual", "median"),
            total_omzet=(kolom_omzet, "sum"),
            median_rating=("rating", "median"),
            median_diskon=("diskon", "median"),
            porsi_pesaing_lemah=(
                "rating",
                lambda r: (r.dropna() < ambang).mean() if r.notna().any() else 0.0,
            ),
        )
        .reset_index()
    )
    ringkasan["omzet_per_produk"] = ringkasan["total_omzet"] / ringkasan["jumlah_produk"]
    return ringkasan


def beri_skor(
    ringkasan: pd.DataFrame,
    bobot: tuple[float, float, float] = (1.0, 1.0, 1.0),
    pakai_log: bool = True,
) -> pd.DataFrame:
    """Hitung skor peluang. Bobot berurutan: permintaan, kompetisi, pesaing lemah."""
    ringkasan = ringkasan.copy()

    # Log dipakai karena nilai penjualan dan jumlah pesaing sangat miring ke
    # kanan: sedikit produk terlaris menguasai sebagian besar volume.
    ubah = np.log1p if pakai_log else (lambda s: s)
    permintaan = _z(ubah(ringkasan["total_omzet"]))
    kompetisi = _z(ubah(ringkasan["jumlah_produk"]))
    pesaing_lemah = _z(ringkasan["porsi_pesaing_lemah"])

    b_permintaan, b_kompetisi, b_lemah = bobot
    skor = b_permintaan * permintaan - b_kompetisi * kompetisi + b_lemah * pesaing_lemah

    ringkasan["skor_peluang"] = skor.round(3)
    ringkasan["skor_permintaan"] = permintaan.round(3)
    ringkasan["skor_kompetisi"] = kompetisi.round(3)
    ringkasan["skor_pesaing_lemah"] = pesaing_lemah.round(3)

    return ringkasan.sort_values("skor_peluang", ascending=False).reset_index(drop=True)


def ringkas_segmen(listings: pd.DataFrame) -> pd.DataFrame:
    ringkasan = beri_skor(agregasi_segmen(listings))

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    ringkasan.to_csv(DATA_PROCESSED / "segment_summary.csv", index=False, encoding="utf-8")

    print(f"[opportunity] {len(ringkasan)} kombinasi kategori x segmen dinilai")
    return ringkasan


def ringkas_kategori(listings: pd.DataFrame) -> pd.DataFrame:
    ringkasan = (
        listings.groupby("kategori")
        .agg(
            jumlah_produk=("nama_produk", "count"),
            jumlah_penjual=("nama_toko", "nunique"),
            median_harga=("harga", "median"),
            total_terjual=("terjual", "sum"),
            total_omzet=("estimasi_omzet", "sum"),
            median_rating=("rating", "median"),
            median_diskon=("diskon", "median"),
        )
        .reset_index()
        .sort_values("total_omzet", ascending=False)
    )

    # Rasio omzet per produk menunjukkan seberapa "gemuk" tiap listing di
    # kategori itu — proksi kasar untuk daya tarik kategori bagi penjual baru.
    ringkasan["omzet_per_produk"] = ringkasan["total_omzet"] / ringkasan["jumlah_produk"]

    ringkasan.to_csv(DATA_PROCESSED / "category_summary.csv", index=False, encoding="utf-8")
    return ringkasan
