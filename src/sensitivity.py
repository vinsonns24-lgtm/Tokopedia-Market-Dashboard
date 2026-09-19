"""Uji sensitivitas skor peluang: seberapa kokoh peringkatnya?

Skor peluang tidak punya kunci jawaban, jadi tidak bisa divalidasi seperti
model. Yang bisa diuji adalah apakah peringkatnya bertahan ketika hal-hal yang
seharusnya tidak penting diubah. Ada dua sumber ketidakpastian yang berbeda:

1. Pilihan desain — ambang 4,7, bobot komponen, transformasi log, persentil
   pemangkasan. Semuanya keputusan yang masuk akal, tapi bukan satu-satunya.
2. Kebetulan sampel — produk mana yang kebetulan ikut ter-scrape. Diuji dengan
   bootstrap: ambil ulang sampel produk dengan pengembalian, hitung ulang skor.

Bootstrap mengukur *variasi* sampel, bukan *bias*-nya. Kalau otomotif memang
jarang ter-scrape, setiap sampel ulang mewarisi kekurangan yang sama.
"""

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from . import clean_listings, opportunity
from .config import DATA_PROCESSED

KUNCI = ["kategori", "segmen_harga"]

# Tiap variasi mengubah satu hal dari versi dasar. Rentangnya dipilih sebagai
# alternatif yang sama-sama bisa dibela, bukan nilai ekstrem.
VARIASI_DESAIN = {
    "Ambang 4,5": dict(ambang=4.5),
    "Ambang 4,6": dict(ambang=4.6),
    "Ambang 4,8": dict(ambang=4.8),
    "Ambang 4,9": dict(ambang=4.9),
    "Bobot permintaan ×0,5": dict(bobot=(0.5, 1, 1)),
    "Bobot permintaan ×2": dict(bobot=(2, 1, 1)),
    "Bobot kompetisi ×0,5": dict(bobot=(1, 0.5, 1)),
    "Bobot kompetisi ×2": dict(bobot=(1, 2, 1)),
    "Bobot pesaing lemah ×0,5": dict(bobot=(1, 1, 0.5)),
    "Bobot pesaing lemah ×2": dict(bobot=(1, 1, 2)),
    "Tanpa transformasi log": dict(pakai_log=False),
    "Pemangkasan di P99": dict(persentil=0.99),
    "Pemangkasan di P99,9": dict(persentil=0.999),
}

ABLASI = {
    "Tanpa permintaan": (0, 1, 1),
    "Tanpa kompetisi": (1, 0, 1),
    "Tanpa pesaing lemah": (1, 1, 0),
}


def skor(
    listings: pd.DataFrame,
    ambang: float = opportunity.AMBANG_PESAING_LEMAH,
    bobot: tuple[float, float, float] = (1.0, 1.0, 1.0),
    pakai_log: bool = True,
    persentil: float | None = None,
) -> pd.DataFrame:
    """Skor peluang dengan satu asumsi diganti, diindeks per kategori x segmen."""
    kolom = "estimasi_omzet"
    if persentil is not None:
        listings = listings.assign(
            omzet_uji=clean_listings.pangkas_per_kategori(listings, persentil)
        )
        kolom = "omzet_uji"

    hasil = opportunity.beri_skor(
        opportunity.agregasi_segmen(listings, ambang, kolom), bobot, pakai_log
    )
    hasil["peringkat"] = np.arange(1, len(hasil) + 1)
    return hasil.set_index(KUNCI)


def uji_desain(listings: pd.DataFrame, top_n: int = 5) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Bandingkan tiap variasi desain dengan versi dasar.

    Hasil pertama: satu baris per variasi. Hasil kedua: peringkat tiap segmen
    di tiap variasi, untuk melihat segmen mana yang bertahan.
    """
    dasar = skor(listings)
    top_dasar = set(dasar.head(top_n).index)

    baris, peringkat = [], {"Dasar": dasar["peringkat"]}
    for nama, argumen in VARIASI_DESAIN.items():
        v = skor(listings, **argumen)
        peringkat[nama] = v["peringkat"].reindex(dasar.index)
        baris.append({
            "variasi": nama,
            "korelasi_peringkat": spearmanr(dasar["skor_peluang"],
                                            v["skor_peluang"].reindex(dasar.index))[0],
            f"sama_di_top{top_n}": len(top_dasar & set(v.head(top_n).index)),
            "peringkat_1": " — ".join(v.index[0]),
        })

    return pd.DataFrame(baris), pd.DataFrame(peringkat)


def uji_ablasi(listings: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    """Buang satu komponen, lihat siapa yang naik ke papan atas."""
    dasar = skor(listings)
    top_dasar = set(dasar.head(top_n).index)

    baris = []
    for nama, bobot in ABLASI.items():
        v = skor(listings, bobot=bobot)
        baris.append({
            "komponen dibuang": nama,
            f"sama_di_top{top_n}": len(top_dasar & set(v.head(top_n).index)),
            f"top{top_n}": [" — ".join(i) for i in v.head(top_n).index],
        })
    return pd.DataFrame(baris)


def bootstrap(listings: pd.DataFrame, n: int = 300, seed: int = 42) -> pd.DataFrame:
    """Peringkat tiap segmen di tiap sampel ulang (baris = segmen, kolom = iterasi).

    Yang diambil ulang adalah produk, lalu seluruh proses diulang — termasuk
    batas segmen harga, karena batas itu sendiri bergantung pada sampel.
    """
    dasar = skor(listings)
    rng = np.random.default_rng(seed)

    hasil = []
    for _ in range(n):
        sampel = listings.iloc[rng.integers(0, len(listings), len(listings))]
        hasil.append(skor(sampel.reset_index(drop=True))["peringkat"].reindex(dasar.index))
    return pd.concat(hasil, axis=1, ignore_index=True)


def ringkas_bootstrap(listings: pd.DataFrame, peringkat_boot: pd.DataFrame) -> pd.DataFrame:
    dasar = skor(listings)
    return pd.DataFrame({
        "peringkat": dasar["peringkat"],
        "peringkat_median": peringkat_boot.median(axis=1),
        "peringkat_p5": peringkat_boot.quantile(0.05, axis=1),
        "peringkat_p95": peringkat_boot.quantile(0.95, axis=1),
        "porsi_top1": (peringkat_boot == 1).mean(axis=1),
        "porsi_top5": (peringkat_boot <= 5).mean(axis=1),
        "porsi_top10": (peringkat_boot <= 10).mean(axis=1),
    }).sort_values("peringkat").reset_index()


def jalankan(listings: pd.DataFrame) -> pd.DataFrame:
    """Hitung stabilitas tiap segmen untuk ditampilkan di dashboard."""
    stabilitas = ringkas_bootstrap(listings, bootstrap(listings))

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    stabilitas.to_csv(DATA_PROCESSED / "segment_stability.csv", index=False, encoding="utf-8")

    kokoh = stabilitas[stabilitas["porsi_top5"] >= 0.8]
    print(f"[stabilitas] {len(kokoh)} segmen bertahan di 5 besar pada >=80% sampel ulang: "
          + ", ".join(f"{r.kategori} {r.segmen_harga}" for r in kokoh.itertuples()))
    return stabilitas
