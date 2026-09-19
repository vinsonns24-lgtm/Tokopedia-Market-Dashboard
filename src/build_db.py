"""Memuat hasil olahan ke SQLite agar dashboard bisa query dengan SQL.

Dashboard sengaja membaca dari database, bukan langsung dari CSV, supaya
lapisan penyimpanan dan lapisan tampilan terpisah — pola yang sama dipakai di
sistem produksi.
"""

import sqlite3

import pandas as pd

from .config import DB_PATH

INDEKS = [
    "CREATE INDEX IF NOT EXISTS idx_listings_kategori ON listings(kategori)",
    "CREATE INDEX IF NOT EXISTS idx_listings_lokasi ON listings(lokasi)",
    "CREATE INDEX IF NOT EXISTS idx_reviews_kategori ON reviews(kategori)",
]


def muat(tabel: dict[str, pd.DataFrame]) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        for nama, df in tabel.items():
            df.to_sql(nama, conn, if_exists="replace", index=False)
            print(f"[db] tabel '{nama}': {len(df):,} baris")

        for perintah in INDEKS:
            try:
                conn.execute(perintah)
            except sqlite3.OperationalError as exc:
                print(f"[db] lewati indeks: {exc}")

        conn.commit()

    print(f"[db] database siap di {DB_PATH}")
