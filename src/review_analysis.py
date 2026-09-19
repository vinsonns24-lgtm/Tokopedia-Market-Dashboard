"""Lapisan diagnostik: menjawab *kenapa* pembeli kecewa di tiap kategori.

Memakai dua pendekatan yang saling melengkapi:
1. Pencocokan aturan ke tema keluhan yang sudah didefinisikan. Transparan dan
   bisa dipertanggungjawabkan — setiap angka bisa ditelusuri ke kata pemicunya.
2. TF-IDF untuk menemukan kata menonjol yang mungkin luput dari daftar aturan.

Pendekatan pertama jadi acuan utama; yang kedua dipakai untuk memeriksa apakah
ada tema penting yang belum terdaftar.
"""

import re

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

from .config import COMPLAINT_THEMES, DATA_PROCESSED

_stemmer = StemmerFactory().create_stemmer()
_stopwords = set(StopWordRemoverFactory().get_stop_words())
_cache_stem: dict[str, str] = {}

# Kata yang sering muncul di ulasan tapi tidak membawa informasi keluhan.
STOPWORD_TAMBAHAN = {
    "barang", "produk", "bagus", "terima", "kasih", "ok", "oke", "mantap",
    "sesuai", "pesanan", "beli", "pembelian", "toko", "seller", "banget",
    "bgt", "yg", "ga", "gak", "nggak", "engga", "tdk", "udah", "sdh", "aja",
    "nya", "dgn", "sih", "deh", "kak", "gan", "min", "brg", "trs", "jg",
}


def _stem(kata: str) -> str:
    """Stemming dengan memo per kata — Sastrawi lambat kalau dipanggil per kalimat."""
    if kata not in _cache_stem:
        _cache_stem[kata] = _stemmer.stem(kata)
    return _cache_stem[kata]


# Kata utuh plus akhiran umum ("rusaknya", "dikirimkan"). Pencocokan potongan
# huruf sempat membuat "mati" cocok dengan "otomatis" dan "kw" dengan "kwalitas".
_POLA_TEMA = {
    tema: re.compile(
        r"\b(?:" + "|".join(re.escape(kk) for kk in kata_kunci) + r")(?:nya|kan|an)?\b"
    )
    for tema, kata_kunci in COMPLAINT_THEMES.items()
}


def tandai_tema(ulasan: str) -> list[str]:
    """Satu ulasan bisa memuat lebih dari satu keluhan, jadi hasilnya multi-label."""
    teks = str(ulasan).lower()
    return [tema for tema, pola in _POLA_TEMA.items() if pola.search(teks)]


def hitung_tema_keluhan(reviews: pd.DataFrame) -> pd.DataFrame:
    """Hitung sebaran tema keluhan per kategori, dalam format panjang."""
    negatif = reviews[reviews["is_negatif"]].copy()
    if negatif.empty:
        return pd.DataFrame(columns=["kategori", "tema", "jumlah", "porsi"])

    negatif["tema_list"] = negatif["ulasan"].apply(tandai_tema)

    baris = [
        {"kategori": row.kategori, "tema": tema}
        for row in negatif.itertuples()
        for tema in row.tema_list
    ]
    if not baris:
        return pd.DataFrame(columns=["kategori", "tema", "jumlah", "porsi"])

    tema_df = pd.DataFrame(baris)
    hasil = tema_df.groupby(["kategori", "tema"]).size().reset_index(name="jumlah")

    # Penyebutnya jumlah ulasan negatif per kategori, bukan jumlah label, supaya
    # angkanya terbaca sebagai "sekian persen ulasan negatif menyinggung X".
    total_negatif = negatif.groupby("kategori").size().rename("total_negatif")
    hasil = hasil.merge(total_negatif, on="kategori", how="left")
    hasil["porsi"] = hasil["jumlah"] / hasil["total_negatif"]

    tak_tertandai = (negatif["tema_list"].str.len() == 0).mean()
    print(f"[reviews] ulasan negatif tanpa tema terdeteksi: {tak_tertandai:.1%}")

    return hasil.sort_values(["kategori", "jumlah"], ascending=[True, False])


def kata_menonjol_negatif(reviews: pd.DataFrame, top_n: int = 12) -> pd.DataFrame:
    """Kata dengan skor TF-IDF tertinggi pada ulasan negatif tiap kategori."""
    negatif = reviews[reviews["is_negatif"]]
    if negatif.empty:
        return pd.DataFrame(columns=["kategori", "kata", "skor"])

    stopwords = _stopwords | STOPWORD_TAMBAHAN

    def praproses(teks: str) -> str:
        kata_kata = [k for k in str(teks).lower().split() if k.isalpha() and len(k) > 2]
        kata_kata = [_stem(k) for k in kata_kata]
        return " ".join(k for k in kata_kata if k not in stopwords)

    dokumen_per_kategori = (
        negatif.assign(bersih=negatif["ulasan"].apply(praproses))
        .groupby("kategori")["bersih"]
        .apply(" ".join)
    )

    vectorizer = TfidfVectorizer(max_features=3000, min_df=1)
    matriks = vectorizer.fit_transform(dokumen_per_kategori.values)
    kosakata = vectorizer.get_feature_names_out()

    baris = []
    for i, kategori in enumerate(dokumen_per_kategori.index):
        skor = matriks[i].toarray().ravel()
        indeks_teratas = skor.argsort()[::-1][:top_n]
        baris.extend(
            {"kategori": kategori, "kata": kosakata[j], "skor": float(skor[j])}
            for j in indeks_teratas
            if skor[j] > 0
        )

    return pd.DataFrame(baris)


def jalankan(reviews: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    tema = hitung_tema_keluhan(reviews)
    tema.to_csv(DATA_PROCESSED / "complaint_themes.csv", index=False, encoding="utf-8")

    kata = kata_menonjol_negatif(reviews)
    kata.to_csv(DATA_PROCESSED / "keywords_negatif.csv", index=False, encoding="utf-8")

    print(f"[reviews] {len(tema)} baris tema keluhan, {len(kata)} baris kata menonjol")
    return tema, kata
