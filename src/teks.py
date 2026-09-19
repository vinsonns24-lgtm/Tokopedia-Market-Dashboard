"""Pembersihan teks ulasan.

Dipakai oleh notebook model dan dashboard, supaya teks yang dibaca model
selalu diolah dengan cara yang sama seperti saat model dilatih.
Isinya sama dengan fungsi di notebook 05_data_prep_ulasan.ipynb.
"""

import html
import re

# Singkatan dan ejaan tidak baku yang paling sering muncul, beserta bentuk bakunya
NORMALISASI = {
    "ga": "tidak", "gak": "tidak", "gk": "tidak", "tdk": "tidak", "ngga": "tidak",
    "nggak": "tidak", "engga": "tidak", "enggak": "tidak", "ndak": "tidak", "nda": "tidak",
    "kagak": "tidak", "gag": "tidak", "tak": "tidak",
    "yg": "yang",
    "dgn": "dengan", "dg": "dengan",
    "sdh": "sudah", "udah": "sudah", "udh": "sudah", "dah": "sudah", "sdah": "sudah",
    "uda": "sudah",
    "brg": "barang", "brang": "barang", "barng": "barang", "barangnya": "barang",
    "brng": "barang",
    "bgt": "banget", "bngt": "banget",
    "tp": "tapi", "tpi": "tapi",
    "jg": "juga",
    "blm": "belum", "blum": "belum",
    "krn": "karena", "krna": "karena", "karna": "karena",
    "utk": "untuk", "untk": "untuk",
    "bs": "bisa", "bsa": "bisa",
    "sy": "saya",
    "trs": "terus", "trus": "terus",
    "sm": "sama",
    "klo": "kalau", "kalo": "kalau", "kl": "kalau",
    "aja": "saja", "aj": "saja",
    "bnyk": "banyak",
    "lg": "lagi",
    "org": "orang",
    "pake": "pakai", "pke": "pakai",
    "dipake": "dipakai",
    "gmn": "bagaimana", "gimana": "bagaimana",
    "knp": "kenapa",
    "dr": "dari",
    "msh": "masih",
    "sdikit": "sedikit", "sdkit": "sedikit", "dikit": "sedikit",
    "kcwa": "kecewa",
    "pdhl": "padahal", "pdahal": "padahal",
    "hrs": "harus",
    "bnr": "benar", "bener": "benar",
    "ckp": "cukup",
    "bkn": "bukan",
    "lbh": "lebih",
    "bgs": "bagus",
    "tgl": "tanggal",
    "hr": "hari",
    "jd": "jadi", "jdi": "jadi",
    "sampe": "sampai", "nyampe": "sampai", "nyampai": "sampai", "smpe": "sampai",
    "smp": "sampai",
    "dateng": "datang",
    "cepet": "cepat", "cpt": "cepat",
    "mantab": "mantap", "mantul": "mantap", "mantep": "mantap",
    "oke": "ok", "okay": "ok", "okey": "ok", "okee": "ok",
    "gpp": "tidak apa apa",
    "tq": "terimakasih", "thx": "terimakasih", "thanks": "terimakasih", "thank": "terimakasih",
    "trims": "terimakasih", "makasih": "terimakasih", "mksh": "terimakasih",
    "trimakasih": "terimakasih", "trimakasi": "terimakasih", "makasi": "terimakasih",
    "terimakasi": "terimakasih", "tks": "terimakasih",
    "recomended": "recommended", "rekomended": "recommended", "recommend": "recommended",
    "rekomen": "recommended", "recomend": "recommended", "rekomendasi": "recommended",
    "rapih": "rapi",
    "pengirimannya": "pengiriman",
    "packingnya": "packing",
    "sellernya": "seller", "slr": "seller",
    "ssuai": "sesuai", "sesua": "sesuai",
    "kualitasnya": "kualitas",
    "mf": "maaf", "maap": "maaf",
    "dlm": "dalam",
    "dpt": "dapat",
    "ksh": "kasih",
    "ny": "nya",
    "cm": "cuma",
    "dsni": "disini",
    "sipp": "sip",
    "joss": "jos",
    "yaa": "ya", "yah": "ya",
    "god": "good", "gud": "good",
}


def bersihkan_teks(teks):
    """Membersihkan satu teks ulasan: kode HTML, huruf kecil, tanda baca, huruf berulang, singkatan."""
    teks = html.unescape(str(teks))
    teks = teks.lower()
    teks = teks.replace("terima kasih", "terimakasih")
    teks = re.sub(r"https?://\S+|www\.\S+", " ", teks)
    teks = re.sub(r"[^a-z\s]", " ", teks)
    teks = re.sub(r"([a-z])\1{2,}", r"\1", teks)
    kata = [NORMALISASI.get(k, k) for k in teks.split()]
    return " ".join(kata)
