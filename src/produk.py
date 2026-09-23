"""Data prep listing produk.

Isinya sama dengan langkah-langkah di notebook 02_data_prep_produk.ipynb.
Notebook itu menjelaskan alasan setiap langkah, sedangkan file ini dipakai
oleh run_pipeline.py, test, dan notebook.
"""

import re

import numpy as np
import pandas as pd

KOLOM_BARU = {
    "Nama Produk": "nama_produk",
    "Nama Toko": "nama_toko",
    "Lokasi Toko": "lokasi_toko",
    "Terjual": "terjual_teks",
    "Jumlah Ulasan": "ulasan_teks",
    "Rating": "rating",
    "Harga (IDR)": "harga",
    "Diskon (%)": "diskon",
    "Produk URL": "url",
}

KOLOM_AKHIR = [
    "nama_produk", "kategori", "nama_toko", "lokasi_toko", "kota", "provinsi",
    "harga", "diskon", "terjual", "jumlah_ulasan", "rating", "url",
]

# ---------------------------------------------------------------- angka dari teks

POLA_ANGKA = r"^(\d[\d.,]*)\s*(rb|jt|k)?\s*\+?\s*(?:{kata})?(?:/bln)?$"
PENGALI = {"rb": 1_000, "k": 1_000, "jt": 1_000_000}


def ubah_ke_angka(teks, kata):
    """Mengubah teks seperti '1rb+ terjual' menjadi angka. Hasilnya NaN kalau teks bukan jumlah."""
    if pd.isna(teks):
        return np.nan
    cocok = re.match(POLA_ANGKA.format(kata=kata), teks.strip().lower())
    if cocok is None:
        return np.nan
    angka, satuan = cocok.group(1), cocok.group(2)
    if satuan:
        # Ada satuan: titik atau koma adalah desimal (1.2rb = 1.200)
        return round(float(angka.replace(",", ".")) * PENGALI[satuan])
    # Tanpa satuan: titik atau koma adalah pemisah ribuan (1.000 = 1000)
    return float(angka.replace(".", "").replace(",", ""))


# ---------------------------------------------------------------- lokasi


def rapikan_lokasi(teks):
    """Menyeragamkan nama lokasi, misalnya 'Kota Administrasi Jakarta Barat' menjadi 'Jakarta'."""
    if pd.isna(teks):
        return np.nan
    teks = teks.split(",")[0].strip()
    teks = re.sub(r"^(Kota Administrasi|Kota Adm\.?|Kabupaten|Kab\.?|Kota)\s+", "", teks, flags=re.IGNORECASE)
    teks = re.sub(r"^Jakarta\s+(Barat|Timur|Utara|Selatan|Pusat)$", "Jakarta", teks)
    return teks.strip()


# ---------------------------------------------------------------- kategori

KATEGORI = {
    "Hewan Peliharaan": [
        "dog", "cat food", "cat litter", "kucing", "anjing", "whiskas", "royal canin",
        "akuarium", "aquarium", "aquascape", "ikan hias", "burung", "kandang", "barf",
        # "pet" saja tidak dipakai, karena juga berarti plastik PET (toples, helm, hijab)
        "pet food", "pet shop", "petshop", "pet cargo", "pet carrier", "pet bowl", "raw food",
    ],
    "Otomotif": [
        "motor", "mobil", "helm", "oli", "ban", "velg", "knalpot", "aki", "spion", "honda",
        "yamaha", "toyota", "mitsubishi", "wuling", "hyundai", "suzuki", "kawasaki",
        "daihatsu", "mazda", "vario", "nmax", "karbu", "karburator", "busi", "jok", "brake",
        "kampas rem", "minyak rem",
    ],
    "Handphone": [
        "hp", "handphone", "smartphone", "iphone", "galaxy", "xiaomi", "redmi", "oppo", "vivo",
        "realme", "infinix", "poco", "case hp", "tempered glass", "anti gores", "charger",
        "kabel data", "powerbank", "power bank",
    ],
    "Elektronik": [
        "laptop", "mouse", "keyboard", "monitor", "speaker", "soundbar", "headset", "earphone",
        "headphone", "tws", "bluetooth", "usb", "kabel", "lampu", "led", "kipas", "blender",
        "dispenser", "kulkas", "mesin cuci", "rice cooker", "magic com", "setrika", "vacuum",
        "tv", "televisi", "printer", "router", "kamera", "cctv", "smartwatch", "stop kontak",
        "flashdisk", "ssd", "gaming", "rgb", "ac", "microphone", "mic", "air fryer", "oven",
        "microwave", "ps5", "ps4", "playstation", "nintendo", "rtx", "tripod", "pompa",
        "pompa air", "hdmi", "baterai", "senter", "pc", "komputer", "cpu", "espresso",
        "coffee maker", "toa", "amplifier", "proyektor",
    ],
    "Perhiasan": [
        "cincin", "gelang", "kalung", "anting", "emas", "perak", "liontin", "mutiara",
        "logam mulia", "antam", "akik",
    ],
    "Olahraga": [
        "jersey", "sepeda", "raket", "futsal", "badminton", "yoga", "gym", "dumbbell",
        "barbel", "olahraga", "renang", "matras", "camping", "tenda", "hiking", "pancing",
        "joran", "bola", "cycling", "sarung tangan", "golf", "tenis", "skipping",
        "shuttlecock", "treadmill", "sepatu bola", "carrier",
    ],
    "Ibu, Bayi & Mainan": [
        "mainan", "boneka", "lego", "puzzle", "action figure", "bayi", "baby", "popok",
        "diapers", "stroller", "mpasi", "balita", "edukatif", "figure", "toys", "toy", "asi",
        "bandai", "hot wheels",
    ],
    "Fashion": [
        "baju", "kaos", "kemeja", "celana", "jaket", "hoodie", "sweater", "cardigan", "blouse",
        "dress", "rok", "gamis", "abaya", "hijab", "kerudung", "jilbab", "batik", "piyama",
        "sepatu", "sandal", "sneakers", "shoes", "tas", "bag", "dompet", "ransel", "koper",
        "topi", "jam tangan", "watch", "kacamata", "kaos kaki", "sarung", "tees", "kaus",
        "outer", "tunik", "kebaya", "mukena", "sirwal", "heels", "flatshoes", "socks",
        "selendang", "sabuk", "ikat pinggang", "sweatshirt", "jeans", "legging", "kemko",
        "koko", "pashmina", "boots", "slop", "wedges", "tote", "kardigan", "rompi", "blazer",
        "scarf", "syal", "setelan", "daster", "underwear", "celana dalam", "bra", "singlet",
        "peci", "songkok", "sorban", "ciput", "manset", "t-shirt", "tshirt", "bros",
    ],
    "Kesehatan & Kecantikan": [
        "serum", "skincare", "lipstik", "lip", "cushion", "bedak", "foundation", "maskara",
        "mascara", "eyeliner", "parfum", "perfume", "toner", "sunscreen", "moisturizer",
        "facial", "body wash", "sabun", "shampoo", "sampo", "rambut", "hair", "lotion",
        "cream", "krim", "make up", "makeup", "kosmetik", "deodoran", "pomade", "kuku",
        "masker", "vitamin", "obat", "suplemen", "herbal", "madu", "termometer", "tensimeter",
        "gigi", "odol", "hand sanitizer", "minyak kayu putih", "vape", "liquid", "pod", "tint",
        "blush", "spf", "fragrance", "mist", "scrub", "cica", "whitening", "minyak urut",
        "cajeput", "pembalut", "softex", "maternity", "cologne", "edp", "edt", "essence",
        "cleanser", "micellar", "eyeshadow", "concealer", "primer", "brow", "alis", "pelembab",
        "skin", "lipcream", "lipstick", "soap", "retinol", "oksigen", "deodorant", "balsem",
        "clay mask", "clay stick", "setting spray", "shampo",
    ],
    "Makanan & Minuman": [
        "kopi", "teh", "snack", "keripik", "kripik", "sambal", "saus", "kecap", "bumbu",
        "beras", "gula", "minyak goreng", "susu", "coklat", "cokelat", "mie", "daging", "ayam",
        "frozen", "kue", "sirup", "minuman", "makanan", "biskuit", "sosis", "nugget", "tepung",
        "kurma", "abon", "rendang", "basreng", "kimchi", "jamur", "cemilan", "camilan",
        "permen", "selai", "roti", "keju", "bakso", "seblak", "kacang", "garam", "merica",
        "rempah", "oat", "granola", "cireng", "dimsum", "kerupuk", "mentega", "margarin",
        "sayur", "sayuran", "telur", "buah segar", "segar", "latte",
    ],
    "Buku & Alat Tulis": [
        "buku", "novel", "pulpen", "pena", "pensil", "spidol", "kertas", "alat tulis", "tinta",
        "stabilo", "binder", "id card", "lanyard", "kalender", "stiker", "sticker", "hvs",
        "name tag", "map", "amplop", "penggaris", "penghapus", "crayon", "cat air", "penerbit",
        "komik",
    ],
    "Pertukangan": [
        "bor", "gergaji", "obeng", "tang", "palu", "kunci inggris", "kunci pas", "meteran",
        "las", "cat tembok", "semen", "keramik", "pipa", "paku", "baut", "mur", "gerinda",
        "kompresor", "pahat", "plafon", "pvc", "kran", "keran", "engsel", "tangga", "triplek",
        "lem", "staples", "genteng", "wallpaper", "cat", "gembok", "vinyl", "pagar", "gypsum",
        "wastafel", "closet", "shower", "kloset", "sealant", "amplas", "tandon", "kawat",
        "selang", "kunci pintu", "kunci l", "hex key", "door lock", "kunci ring", "decking",
    ],
    "Rumah Tangga": [
        "meja", "kursi", "lemari", "rak", "kasur", "bantal", "guling", "sprei", "seprai",
        "selimut", "karpet", "keset", "gorden", "tirai", "handuk", "piring", "gelas",
        "mangkok", "mangkuk", "sendok", "panci", "wajan", "kompor", "tumbler", "botol",
        "toples", "ember", "sapu", "pel", "jam dinding", "cermin", "dekorasi", "hiasan", "vas",
        "tanaman", "pot", "sofa", "pewangi", "deterjen", "pembersih", "gantungan", "hanger",
        "sajadah", "tikar", "tisu", "tissue", "payung", "dapur", "kulkas", "bingkai", "lilin",
        "sikat", "kain pel", "jemuran", "pisau", "talenan", "teko", "termos", "wadah", "kotak",
        "celengan", "korek", "benih", "bibit", "pupuk", "tanah", "lap", "bak", "loyang",
        "cetakan", "rantang", "spatula", "saringan", "nampan", "baki", "kompor gas",
        "tudung saji", "sofa bed", "tempat tidur", "ranjang", "bed cover", "sarung bantal",
        "rice box", "keranjang", "lukisan", "kanvas", "kresek", "kantong plastik", "apron",
        "furniture", "benang", "poster", "pajangan", "wall decor", "mimbar", "podium", "bonsai",
    ],
}

# Frasa yang dicek lebih dulu, sebelum semua kategori di atas. Tanpa ini, urutan kategori
# membuat frasa berikut salah golong, misalnya "mobil mobilan" masuk Otomotif karena kata
# "mobil", "rak sepatu" masuk Fashion karena kata "sepatu", dan jam Alexandre Christie masuk
# Elektronik karena kodenya diawali "AC". Urutan di sini juga berpengaruh: frasa mainan dicek
# paling awal ("mainan anak tumbler" tetap mainan), lalu elektronik yang spesifik
# ("vacuum cleaner kasur" tetap elektronik), baru rumah tangga.
FRASA_KHUSUS = {
    "Ibu, Bayi & Mainan": [
        "mobil mobilan", "mobilan", "diecast", "hot wheels", "hotwheels", "mobil rc", "rc car",
        "boneka", "mainan anak", "mainan edukasi",
    ],
    "Elektronik": [
        "smartwatch", "smart watch", "jam tangan pintar", "vacuum cleaner", "penyedot debu",
        "charger laptop", "adaptor laptop", "tas laptop", "mikrofon", "stand mic", "lampu meja",
        "desk lamp",
    ],
    "Rumah Tangga": [
        "rak sepatu", "sarung bantal", "gantungan baju", "kantong plastik", "kantong kresek",
        "kresek", "kasur", "springbed", "spring bed", "tumbler", "termos", "botol minum",
        "kursi gaming", "gaming chair", "parfum laundry", "pewangi pakaian", "meja belajar",
        "meja makan",
    ],
    "Hewan Peliharaan": ["pelet ikan", "makanan ikan", "pakan ikan", "pakan burung"],
    "Kesehatan & Kecantikan": [
        "bibit parfum", "eyeshadow", "sarung tangan plastik", "disposable gloves",
        "sarung tangan medis",
    ],
    "Handphone": ["car charger", "charger mobil", "charger hp", "holder hp", "phone holder"],
    "Fashion": ["jam tangan", "alexandre christie", "alexander christie", "koper"],
    "Pertukangan": ["lantai spc", "spc floor", "pintu aluminium", "balok kayu", "kusen"],
    "Otomotif": ["karpet mobil", "tankpad"],
}


def _pola(kata):
    return re.compile(r"\b(" + "|".join(re.escape(k) for k in kata) + r")\b")


POLA_KHUSUS = {kat: _pola(kata) for kat, kata in FRASA_KHUSUS.items()}
POLA_KATEGORI = {kat: _pola(kata) for kat, kata in KATEGORI.items()}


def tentukan_kategori(nama):
    """Kategori dari nama produk.

    Frasa khusus dicek lebih dulu. Kalau tidak ada yang cocok, dipakai kategori pertama
    yang kata kuncinya muncul di nama produk. Kalau tetap tidak ada, hasilnya 'Lainnya'.
    """
    nama = str(nama).lower()
    for pola_per_kategori in (POLA_KHUSUS, POLA_KATEGORI):
        for kat, pola in pola_per_kategori.items():
            if pola.search(nama):
                return kat
    return "Lainnya"


# ---------------------------------------------------------------- seluruh langkah


def bersihkan_produk(mentah, referensi):
    """Menjalankan semua langkah data prep produk.

    mentah: isi Dataset/raw/produk_tokopedia.csv
    referensi: isi Dataset/raw/referensi_kota_provinsi.csv
    Mengembalikan (data bersih, jejak jumlah baris per langkah).
    """
    df = mentah.rename(columns=KOLOM_BARU)
    jejak = {"Data awal": len(df)}

    df = df.drop_duplicates().reset_index(drop=True)
    jejak["Setelah buang duplikat"] = len(df)

    df = df[df["harga"] != 0].reset_index(drop=True)
    jejak["Setelah buang harga 0"] = len(df)

    df["terjual"] = df["terjual_teks"].map(lambda t: ubah_ke_angka(t, "terjual|sold")).astype("Int64")
    df["jumlah_ulasan"] = df["ulasan_teks"].map(lambda t: ubah_ke_angka(t, "(?:total )?ulasan")).astype("Int64")

    df.loc[df["rating"] == 0, "rating"] = np.nan

    df["lokasi_rapi"] = df["lokasi_toko"].map(rapikan_lokasi)
    df = df.merge(referensi, left_on="lokasi_rapi", right_on="lokasi", how="left")

    df["kategori"] = df["nama_produk"].map(tentukan_kategori)

    df = df[KOLOM_AKHIR]
    jejak["Data bersih"] = len(df)
    return df, jejak
