"""Membersihkan dataset listing Tokopedia dan menurunkan kategori dari nama produk.

Tiga pekerjaan utama:
1. Mengubah kolom teks ("1rb+ terjual", "Rp1.234.567") menjadi angka.
2. Menyeragamkan penulisan lokasi toko.
3. Menurunkan kategori dari nama produk, karena dataset ini tidak punya kolom
   kategori sementara dataset ulasan punya. Tanpa langkah ini kedua dataset
   tidak bisa dibandingkan sama sekali.
"""

import re

import pandas as pd

from .config import CATEGORY_KEYWORDS, DATA_PROCESSED, LISTINGS_CLEAN, LISTINGS_RAW

COLUMN_MAP = {
    "Nama Produk": "nama_produk",
    "Nama Toko": "nama_toko",
    "Lokasi Toko": "lokasi_toko",
    "Terjual": "terjual_raw",
    "Jumlah Ulasan": "jumlah_ulasan",
    "Rating": "rating",
    "Harga (IDR)": "harga_raw",
    "Diskon (%)": "diskon_raw",
    "Produk URL": "produk_url",
}

LOKASI_PREFIX = re.compile(r"^(kota administrasi|kota|kabupaten|kab\.?)\s+", re.IGNORECASE)

# Nama provinsi yang kadang ditempel setelah koma: "Jakarta Barat, Dki Jakarta".
PROVINSI = {
    "dki jakarta", "jawa barat", "jawa tengah", "jawa timur", "banten",
    "di yogyakarta", "bali", "sumatera utara", "sumatera barat", "riau",
    "sumatera selatan", "lampung", "kalimantan timur", "sulawesi selatan",
}
# Bukan nama kota — dipakai toko yang tidak menyebut lokasi spesifik.
LOKASI_TAK_SPESIFIK = {"indonesia", "online", "-", ""}

# Batas persentil untuk memangkas estimasi nilai penjualan per produk. Satu
# listing mobil Rp900 juta berlabel "9rb+ terjual" sempat menyumbang 51% total
# nilai pasar; tanpa pemangkasan, satu baris janggal membelokkan seluruh hasil.
PERSENTIL_PANGKAS = 0.995


def parse_terjual(value) -> float:
    """Ubah '1rb+ terjual' menjadi 1000, atau '10 ulasan' menjadi 10.

    Tokopedia menampilkan jumlah terjual sebagai perkiraan bertingkat, bukan
    angka pasti. Hasil konversi ini karena itu adalah batas bawah: '1rb+'
    berarti minimal 1000, bisa jadi 1900.
    """
    if pd.isna(value):
        return 0.0

    teks = (
        str(value).lower()
        .replace("terjual", "").replace("ulasan", "").replace("+", "")
        .strip()
    )
    if not teks:
        return 0.0

    pengali = 1
    if "rb" in teks:
        pengali = 1_000
        teks = teks.replace("rb", "")
    elif "jt" in teks:
        pengali = 1_000_000
        teks = teks.replace("jt", "")

    teks = teks.replace(",", ".").strip()
    angka = re.search(r"\d+(?:\.\d+)?", teks)
    if not angka:
        return 0.0
    return float(angka.group()) * pengali


def parse_harga(value) -> float:
    """Ubah 'Rp1.234.567' atau '1234567' menjadi float."""
    if pd.isna(value):
        return float("nan")
    if isinstance(value, (int, float)):
        return float(value)

    teks = str(value).lower().replace("rp", "").replace(" ", "").strip()
    # Titik di harga Indonesia adalah pemisah ribuan, bukan desimal.
    teks = teks.replace(".", "").replace(",", ".")
    angka = re.search(r"\d+(?:\.\d+)?", teks)
    if not angka:
        return float("nan")
    return float(angka.group())


def parse_persen(value) -> float:
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    angka = re.search(r"\d+(?:[.,]\d+)?", str(value).replace(",", "."))
    return float(angka.group()) if angka else 0.0


def normalisasi_lokasi(value) -> str:
    """Seragamkan 'Kota Jakarta Barat', 'JAKARTA BARAT', 'Pancoran, Kota Jakarta Selatan'.

    Untuk nilai berkoma, bagian yang berupa nama provinsi dibuang dan diambil
    bagian terakhir yang tersisa — itu level kota, bukan kecamatan.
    """
    if pd.isna(value):
        return "Tidak Diketahui"

    bagian = [LOKASI_PREFIX.sub("", b.strip()).strip() for b in str(value).split(",")]
    bagian = [b for b in bagian if b and b.lower() not in PROVINSI]
    if not bagian:
        teks = str(value).split(",")[0].strip()
        bagian = [LOKASI_PREFIX.sub("", teks)]

    kota = bagian[-1].lower()
    if kota in LOKASI_TAK_SPESIFIK:
        return "Tidak Diketahui"
    if kota in {"jakarta administrasi", "dki jakarta"}:
        return "Jakarta"
    return kota.title()


def tentukan_wilayah(lokasi: str) -> str:
    """Gabungkan lima kota administrasi Jakarta, karena banyak toko hanya menulis 'Jakarta'."""
    return "DKI Jakarta" if lokasi.startswith("Jakarta") else lokasi


# Dicocokkan sebagai kata utuh. Pencocokan potongan huruf sempat membuat "mur"
# (pertukangan) cocok dengan "murah" dan "tang" cocok dengan "jam tangan".
_POLA_KATEGORI = {
    kategori: [(re.compile(rf"\b{re.escape(kk)}\b"), len(kk)) for kk in kata_kunci]
    for kategori, kata_kunci in CATEGORY_KEYWORDS.items()
}


def tentukan_kategori(nama_produk) -> str:
    """Tentukan kategori dari nama produk lewat pencocokan kata kunci berbobot.

    Bobotnya adalah panjang kata kunci, sehingga frasa spesifik selalu menang
    atas kata umum: 'sepatu bola' (olahraga, 11) mengalahkan 'sepatu' (fashion, 6).
    """
    if pd.isna(nama_produk):
        return "lainnya"

    teks = str(nama_produk).lower()
    skor = {}
    for kategori, pola_list in _POLA_KATEGORI.items():
        total = sum(bobot for pola, bobot in pola_list if pola.search(teks))
        if total:
            skor[kategori] = total

    if not skor:
        return "lainnya"
    return max(skor, key=skor.get)


def pangkas_per_kategori(df: pd.DataFrame, persentil: float = PERSENTIL_PANGKAS) -> pd.Series:
    """Pangkas estimasi nilai penjualan di persentil tertentu, per kategori (winsorizing).

    Outlier tidak dibuang, hanya dibatasi, sehingga jumlah produk tetap utuh.
    Batasnya per kategori karena "wajar" untuk handphone berbeda dengan untuk obeng.
    """
    batas = df.groupby("kategori")["estimasi_omzet_mentah"].transform(
        lambda s: s.quantile(persentil)
    )
    return df["estimasi_omzet_mentah"].clip(upper=batas)


def bersihkan() -> pd.DataFrame:
    df = pd.read_csv(LISTINGS_RAW, encoding="utf-8", on_bad_lines="skip")
    df = df.rename(columns=COLUMN_MAP)

    wajib = set(COLUMN_MAP.values())
    hilang = wajib - set(df.columns)
    if hilang:
        raise ValueError(
            f"Kolom berikut tidak ditemukan di CSV: {sorted(hilang)}. "
            f"Kolom yang ada: {list(df.columns)}"
        )

    df["harga"] = df["harga_raw"].apply(parse_harga)
    df["terjual"] = df["terjual_raw"].apply(parse_terjual)
    df["diskon"] = df["diskon_raw"].apply(parse_persen)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    # Rating 0 berarti produk belum pernah dinilai, bukan dinilai terburuk.
    df.loc[df["rating"] == 0, "rating"] = float("nan")
    # Kosong berarti tidak ditampilkan, bukan nol — produk seperti itu tetap
    # punya rating. Jadi dibiarkan kosong, tidak diisi 0.
    df["jumlah_ulasan"] = df["jumlah_ulasan"].apply(
        lambda v: parse_terjual(v) if pd.notna(v) else float("nan")
    )
    df["lokasi"] = df["lokasi_toko"].apply(normalisasi_lokasi)
    df["wilayah"] = df["lokasi"].apply(tentukan_wilayah)
    df["kategori"] = df["nama_produk"].apply(tentukan_kategori)

    sebelum = len(df)
    df = df[df["harga"].notna() & (df["harga"] > 0)].copy()
    dibuang = sebelum - len(df)

    # Perkiraan nilai transaksi, dipakai sebagai proksi ukuran pasar karena
    # dataset tidak menyediakan omzet. Nilai mentahnya disimpan, lalu dipangkas
    # per kategori (winsorizing): outlier tidak dibuang, hanya dibatasi.
    df["estimasi_omzet_mentah"] = df["harga"] * df["terjual"]
    df["estimasi_omzet"] = pangkas_per_kategori(df)
    df["dipangkas"] = df["estimasi_omzet_mentah"] > df["estimasi_omzet"]

    kolom_final = [
        "nama_produk", "nama_toko", "lokasi", "wilayah", "kategori", "harga",
        "terjual", "estimasi_omzet", "estimasi_omzet_mentah", "dipangkas",
        "rating", "jumlah_ulasan", "diskon", "produk_url",
    ]
    df = df[kolom_final].reset_index(drop=True)

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(LISTINGS_CLEAN, index=False, encoding="utf-8")

    print(f"[listings] {len(df):,} baris bersih ({dibuang:,} dibuang karena harga tidak valid)")
    total_mentah = df["estimasi_omzet_mentah"].sum()
    print(
        f"[listings] {df['dipangkas'].sum():,} produk dipangkas nilainya; total nilai "
        f"pasar turun {1 - df['estimasi_omzet'].sum() / total_mentah:.0%}"
    )
    print(f"[listings] sebaran kategori:\n{df['kategori'].value_counts().to_string()}")
    return df


if __name__ == "__main__":
    bersihkan()
