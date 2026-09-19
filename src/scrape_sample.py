"""Komponen scraping ringan — dengan pengecekan robots.txt lebih dulu.

Script ini sengaja memeriksa robots.txt dan berhenti kalau aksesnya dilarang.
Hasil pemeriksaan itu sendiri adalah temuan yang dicatat, bukan rintangan yang
diakali. Portofolio yang menampilkan pertimbangan etika pengumpulan data lebih
bernilai daripada yang sekadar menembus proteksi.
"""

import time
import urllib.robotparser
from urllib.parse import urlparse

import pandas as pd
import requests

from .config import DATA_PROCESSED, SCRAPE_RESULT

USER_AGENT = "Mozilla/5.0 (compatible; PortfolioResearchBot/1.0; +edukasi)"
JEDA_DETIK = 2.0  # jeda antar permintaan, jauh di bawah ambang beban server
BATAS_SAMPEL = 20


def cek_robots(url_contoh: str) -> tuple[bool, str]:
    """Periksa apakah robots.txt mengizinkan pengambilan URL ini."""
    parsed = urlparse(url_contoh)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(robots_url)
    try:
        parser.read()
    except Exception as exc:
        return False, f"robots.txt tidak bisa dibaca ({exc}) — dianggap tidak mengizinkan"

    diizinkan = parser.can_fetch(USER_AGENT, url_contoh)
    status = "mengizinkan" if diizinkan else "melarang"
    return diizinkan, f"robots.txt di {robots_url} {status} pengambilan {parsed.path}"


def ambil_sampel(urls: list[str], batas: int = BATAS_SAMPEL) -> pd.DataFrame:
    if not urls:
        print("[scrape] tidak ada URL untuk diperiksa")
        return pd.DataFrame()

    diizinkan, catatan = cek_robots(urls[0])
    print(f"[scrape] {catatan}")

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    if not diizinkan:
        hasil = pd.DataFrame(
            [{
                "url": urls[0],
                "status": "dilewati",
                "catatan": catatan,
                "keputusan": "Scraping tidak dilanjutkan karena dilarang robots.txt.",
            }]
        )
        hasil.to_csv(SCRAPE_RESULT, index=False, encoding="utf-8")
        print("[scrape] dihentikan sesuai robots.txt — keputusan dicatat ke CSV")
        return hasil

    baris = []
    sesi = requests.Session()
    sesi.headers.update({"User-Agent": USER_AGENT})

    for url in urls[:batas]:
        try:
            resp = sesi.get(url, timeout=10)
            baris.append({
                "url": url,
                "status": resp.status_code,
                "panjang_html": len(resp.text),
                "catatan": "berhasil" if resp.ok else "ditolak server",
            })
        except Exception as exc:
            baris.append({"url": url, "status": "error", "panjang_html": 0, "catatan": str(exc)})

        time.sleep(JEDA_DETIK)

    hasil = pd.DataFrame(baris)
    hasil.to_csv(SCRAPE_RESULT, index=False, encoding="utf-8")
    print(f"[scrape] {len(hasil)} URL diperiksa")
    return hasil
