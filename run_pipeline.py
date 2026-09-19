"""Jalankan seluruh pipeline: bersihkan data, hitung metrik, isi database.

Pakai:
    python run_pipeline.py            # pipeline penuh
    python run_pipeline.py --scrape   # sekalian uji komponen scraping
"""

import sys

from src import (build_db, clean_listings, clean_reviews, opportunity, review_analysis,
                 sensitivity, sentiment_model)
from src.config import LISTINGS_RAW, REVIEWS_RAW


def main(dengan_scraping: bool = False) -> None:
    for berkas in (LISTINGS_RAW, REVIEWS_RAW):
        if not berkas.exists():
            print(f"ERROR: {berkas} tidak ditemukan.")
            print("Unduh kedua CSV dari Kaggle ke folder data/raw/ — lihat README.")
            sys.exit(1)

    print("=" * 60)
    print("1/6  Membersihkan data listing")
    listings = clean_listings.bersihkan()

    print("\n2/6  Membersihkan data ulasan")
    reviews = clean_reviews.bersihkan()

    print("\n3/6  Menghitung skor peluang per segmen dan menguji kestabilannya")
    ringkasan_segmen = opportunity.ringkas_segmen(listings)
    ringkasan_kategori = opportunity.ringkas_kategori(listings)
    listings_tersegmen = opportunity.beri_segmen_harga(listings)
    stabilitas_segmen = sensitivity.jalankan(listings)

    print("\n4/6  Menganalisis ulasan negatif")
    tema, kata_kunci = review_analysis.jalankan(reviews)

    print("\n5/6  Melatih model sentimen")
    sentiment_model.latih(reviews)

    print("\n6/6  Memuat ke SQLite")
    build_db.muat({
        "listings": listings,
        "listings_segmented": listings_tersegmen,
        "segment_summary": ringkasan_segmen,
        "segment_stability": stabilitas_segmen,
        "category_summary": ringkasan_kategori,
        "reviews": reviews,
        "complaint_themes": tema,
        "keywords_negatif": kata_kunci,
    })

    if dengan_scraping:
        print("\nTambahan  Menguji komponen scraping")
        from src import scrape_sample
        scrape_sample.ambil_sampel(listings["produk_url"].dropna().tolist())

    print("\n" + "=" * 60)
    print("Selesai. Jalankan dashboard dengan:  streamlit run app.py")


if __name__ == "__main__":
    main(dengan_scraping="--scrape" in sys.argv)
