"""Membersihkan dataset ulasan Tokopedia dan menandai ulasan negatif."""

import pandas as pd

from .config import DATA_PROCESSED, NEGATIVE_RATING_MAX, REVIEWS_CLEAN, REVIEWS_RAW

KOLOM_HARAPAN = ["text", "rating", "category", "product_name", "product_id", "sold", "shop_id"]


def bersihkan() -> pd.DataFrame:
    df = pd.read_csv(REVIEWS_RAW, encoding="utf-8", on_bad_lines="skip")

    hilang = [k for k in KOLOM_HARAPAN if k not in df.columns]
    if hilang:
        raise ValueError(
            f"Kolom berikut tidak ditemukan di CSV ulasan: {hilang}. "
            f"Kolom yang ada: {list(df.columns)}"
        )

    df = df.rename(
        columns={
            "text": "ulasan",
            "rating": "rating",
            "category": "kategori",
            "product_name": "nama_produk",
            "product_id": "produk_id",
            "sold": "terjual",
            "shop_id": "toko_id",
        }
    )

    sebelum = len(df)
    df["ulasan"] = df["ulasan"].astype(str).str.strip()
    df = df[df["ulasan"].notna() & (df["ulasan"].str.len() > 0) & (df["ulasan"] != "nan")]

    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df = df[df["rating"].between(1, 5)]

    df["kategori"] = df["kategori"].astype(str).str.lower().str.strip()
    df["panjang_ulasan"] = df["ulasan"].str.len()
    df["is_negatif"] = df["rating"] <= NEGATIVE_RATING_MAX

    kolom_final = [
        "ulasan", "rating", "kategori", "nama_produk", "produk_id",
        "terjual", "toko_id", "panjang_ulasan", "is_negatif",
    ]
    df = df[[k for k in kolom_final if k in df.columns]].reset_index(drop=True)

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(REVIEWS_CLEAN, index=False, encoding="utf-8")

    dibuang = sebelum - len(df)
    print(f"[reviews] {len(df):,} ulasan bersih ({dibuang:,} dibuang karena kosong/rating tidak valid)")
    print(f"[reviews] porsi ulasan negatif: {df['is_negatif'].mean():.1%}")
    return df


if __name__ == "__main__":
    bersihkan()
