"""Membuat ulang data bersih dari data mentah.

Pemakaian (dari folder utama proyek):
    python run_pipeline.py

Hasilnya:
    Dataset/processed/produk_bersih.csv
    Dataset/processed/ulasan_bersih.csv

Model sentimen tidak dilatih ulang di sini. Model dilatih di notebook
Notebooks/06_model_sentimen.ipynb dan disimpan di folder models/.
"""

from pathlib import Path

import pandas as pd

from src.produk import bersihkan_produk
from src.ulasan import bersihkan_ulasan

RAW = Path("Dataset/raw")
PROCESSED = Path("Dataset/processed")


def cetak_jejak(nama, jejak):
    print(nama)
    for langkah, jumlah in jejak.items():
        print(f"  {langkah:<28}{jumlah:>8,}".replace(",", "."))


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)

    produk, jejak = bersihkan_produk(
        pd.read_csv(RAW / "produk_tokopedia.csv"),
        pd.read_csv(RAW / "referensi_kota_provinsi.csv"),
    )
    produk.to_csv(PROCESSED / "produk_bersih.csv", index=False)
    cetak_jejak("Produk", jejak)

    ulasan, jejak = bersihkan_ulasan(pd.read_csv(RAW / "tokopedia-product-reviews-2019.csv"))
    ulasan.to_csv(PROCESSED / "ulasan_bersih.csv", index=False)
    cetak_jejak("Ulasan", jejak)


if __name__ == "__main__":
    main()
