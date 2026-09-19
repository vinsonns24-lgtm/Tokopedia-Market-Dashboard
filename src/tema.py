"""Tema yang dibahas dalam ulasan, ditentukan dari kata kunci.

Isinya sama dengan kamus TEMA di notebook 07_analisis_ulasan.ipynb.
Satu ulasan bisa masuk lebih dari satu tema.
"""

TEMA = {
    "Pengiriman": ["kirim", "dikirim", "pengiriman", "kurir", "ekspedisi", "jne", "jnt", "sicepat",
                   "ongkir", "datang", "sampai", "nyampe", "lama", "telat", "terlambat", "cepat"],
    "Kemasan": ["packing", "bubble", "wrap", "kardus", "dus", "bungkus", "kemasan", "dikemas",
                "packaging", "penyok"],
    "Kualitas produk": ["kualitas", "awet", "kuat", "rusak", "jelek", "mati", "pecah", "cacat",
                        "berfungsi", "fungsi", "ori", "original", "palsu", "kw", "bahan", "tipis",
                        "tebal", "patah", "bocor", "lecet"],
    "Kesesuaian pesanan": ["sesuai", "deskripsi", "gambar", "foto", "beda", "berbeda", "warna",
                           "ukuran", "size", "model", "kurang", "salah", "tertukar"],
    "Pelayanan penjual": ["respon", "respons", "seller", "penjual", "admin", "chat", "ramah", "balas",
                          "dibalas", "pelayanan", "komunikatif", "responsif"],
    "Harga": ["harga", "murah", "mahal", "worth", "diskon", "promo", "hemat"],
}


def tandai_tema(teks_bersih):
    """Menerima Series teks yang sudah dibersihkan, mengembalikan DataFrame True/False per tema."""
    import pandas as pd

    kata_ulasan = teks_bersih.fillna("").str.split().map(set)
    return pd.DataFrame({
        tema: kata_ulasan.map(lambda kata, kunci=kata_kunci: not kata.isdisjoint(kunci))
        for tema, kata_kunci in TEMA.items()
    })
