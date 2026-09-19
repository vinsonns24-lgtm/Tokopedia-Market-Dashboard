"""Data prep ulasan.

Isinya sama dengan langkah-langkah di notebook 05_data_prep_ulasan.ipynb.
"""

import html

import numpy as np

from src.teks import bersihkan_teks

KOLOM_BARU = {
    "text": "teks",
    "category": "kategori",
    "product_name": "nama_produk",
    "product_id": "id_produk",
    "shop_id": "id_toko",
    "product_url": "url",
}

KOLOM_AKHIR = ["teks", "teks_bersih", "label", "rating", "kategori", "nama_produk", "id_produk", "id_toko", "url"]


def bersihkan_ulasan(mentah):
    """Menjalankan semua langkah data prep ulasan.

    mentah: isi Dataset/raw/tokopedia-product-reviews-2019.csv
    Mengembalikan (data bersih, jejak jumlah baris per langkah).
    """
    df = mentah.drop(columns=["Unnamed: 0", "sold"]).rename(columns=KOLOM_BARU)
    df["nama_produk"] = df["nama_produk"].map(html.unescape)
    jejak = {"Data awal": len(df)}

    df = df.drop_duplicates(subset=["teks", "id_produk"]).reset_index(drop=True)
    jejak["Setelah buang duplikat"] = len(df)

    df = df[df["rating"] != 3].copy()
    df["label"] = np.where(df["rating"] <= 2, "negatif", "positif")
    jejak["Setelah buang bintang 3"] = len(df)

    df["teks_bersih"] = df["teks"].map(bersihkan_teks)
    df = df[df["teks_bersih"].str.strip() != ""].reset_index(drop=True)
    jejak["Setelah buang teks kosong"] = len(df)

    df = df[KOLOM_AKHIR]
    jejak["Data bersih"] = len(df)
    return df, jejak
