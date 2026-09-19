"""Data sintetis kecil, supaya test bisa jalan tanpa dataset Kaggle."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def listings_sintetis() -> pd.DataFrame:
    """Tiga kategori dengan rentang harga yang sangat berbeda, 40 produk masing-masing."""
    rng = np.random.default_rng(0)
    baris = []
    for kategori, harga_dasar in [("fashion", 50_000), ("handphone", 2_000_000), ("otomotif", 500_000)]:
        for i in range(40):
            harga = harga_dasar * (0.5 + i / 20)
            terjual = float(rng.integers(1, 500))
            baris.append({
                "nama_produk": f"{kategori} {i}",
                "nama_toko": f"toko {i % 7}",
                "kategori": kategori,
                "harga": harga,
                "terjual": terjual,
                "estimasi_omzet_mentah": harga * terjual,
                "estimasi_omzet": harga * terjual,
                "rating": rng.choice([np.nan, 4.2, 4.6, 4.8, 4.9, 5.0]),
                "diskon": 0.0,
            })
    return pd.DataFrame(baris)
