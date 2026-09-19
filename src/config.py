"""Konfigurasi terpusat: path, taksonomi kategori, dan tema keluhan."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
DB_PATH = ROOT / "database.db"

LISTINGS_RAW = DATA_RAW / "produk_tokopedia.csv"
REVIEWS_RAW = DATA_RAW / "tokopedia-product-reviews-2019.csv"

LISTINGS_CLEAN = DATA_PROCESSED / "listings_clean.csv"
REVIEWS_CLEAN = DATA_PROCESSED / "reviews_clean.csv"
SCRAPE_RESULT = DATA_PROCESSED / "scrape_sample.csv"

MODELS_DIR = ROOT / "models"
SENTIMENT_MODEL = MODELS_DIR / "sentiment.joblib"
SENTIMENT_METRICS = MODELS_DIR / "sentiment_metrics.json"

# Lima kategori ini mengikuti taksonomi dataset ulasan. Dataset listing tidak
# punya kolom kategori, jadi kategorinya diturunkan dari nama produk agar kedua
# dataset bisa dibandingkan pada level yang sama.
REVIEW_CATEGORIES = ["handphone", "elektronik", "fashion", "olahraga", "pertukangan"]

# Kata kunci per kategori, dicocokkan sebagai kata utuh (bukan potongan huruf,
# agar "mur" tidak cocok dengan "murah"). Bobotnya panjang kata kunci, sehingga
# frasa spesifik ("sepatu bola") mengalahkan kata umum ("sepatu").
#
# Lima kategori pertama mengikuti dataset ulasan. Sisanya ada karena dataset
# listing adalah marketplace umum; tanpa kategori tambahan, lebih dari separuh
# produk tidak terklasifikasi. Kategori tambahan hanya muncul di lapis 1-2.
CATEGORY_KEYWORDS = {
    "handphone": [
        "handphone", "smartphone", "iphone", "samsung galaxy", "xiaomi", "redmi",
        "oppo", "vivo", "realme", "infinix", "poco", "tecno", "itel", "nokia",
        "anti gores", "tempered glass", "softcase", "hardcase", "case hp",
        "casing hp", "powerbank", "power bank", "charger hp", "kabel data",
        "simcard", "sim card", "kartu perdana", "holder hp", "popsocket", "hp",
        "charger", "casing", "case",
    ],
    "elektronik": [
        "laptop", "notebook", "macbook", "komputer", "pc gaming", "monitor",
        "keyboard", "mouse", "flashdisk", "flash disk", "hardisk", "harddisk",
        "ssd", "printer", "televisi", "smart tv", "kulkas", "mesin cuci",
        "rice cooker", "magic com", "magicom", "blender", "mixer", "microwave",
        "oven", "dispenser", "setrika", "kipas angin", "air cooler", "speaker",
        "headset", "earphone", "headphone", "tws", "kamera", "webcam",
        "proyektor", "stabilizer", "lampu led", "cctv", "router", "modem",
        "hair dryer", "catokan", "kompor listrik", "kabel", "adaptor",
        "stop kontak", "baterai", "console", "playstation", "nintendo",
        "joystick", "gamepad",
    ],
    "fashion": [
        "kaos", "kemeja", "baju", "blouse", "dress", "gamis", "hijab", "jilbab",
        "kerudung", "celana", "jeans", "rok", "jaket", "hoodie", "sweater",
        "cardigan", "sepatu", "sneakers", "sandal", "high heels", "tas",
        "ransel", "dompet", "ikat pinggang", "kacamata", "jam tangan",
        "kaos kaki", "topi", "syal", "piyama", "daster", "batik", "koko",
        "mukena", "abaya", "outer", "tunik", "kulot", "legging", "rompi",
        "cincin", "kalung", "gelang", "anting", "scrunchie", "ikat rambut",
        "jepit rambut", "bros", "sarung", "gantungan kunci",
    ],
    "olahraga": [
        "bola sepak", "bola basket", "bola voli", "sepatu bola", "sepatu futsal",
        "jersey", "raket badminton", "raket tenis", "shuttlecock", "kok badminton",
        "sepeda", "helm sepeda", "dumbell", "dumbbell", "barbel", "matras yoga",
        "yoga mat", "treadmill", "skipping", "resistance band", "sarung tinju",
        "kacamata renang", "baju renang", "pelampung", "fitness", "gym",
        "raket", "decker", "shin guard", "tali skipping",
    ],
    "pertukangan": [
        "obeng", "tang", "palu", "gergaji", "kunci pas", "kunci inggris",
        "kunci sok", "meteran", "waterpass", "bor listrik", "mata bor",
        "gerinda", "amplas", "paku", "sekrup", "baut", "mur", "lem kayu",
        "cat tembok", "kuas cat", "roll cat", "las listrik", "kawat las",
        "cutter", "gunting seng", "tool kit", "toolkit", "tangga lipat",
        "selang air", "keran", "pipa pvc", "engsel", "gembok", "sealant",
        "pompa air", "pompa celup", "tangga", "kunci", "lem",
    ],
    "rumah tangga": [
        "meja", "kursi", "lemari", "rak", "kasur", "bantal", "guling",
        "sarung bantal", "sprei", "selimut", "karpet", "keset", "gorden",
        "handuk", "cermin", "jam dinding", "lampu", "lampu tidur", "sapu",
        "pel", "mop", "ember", "tempat sampah", "gantungan baju", "hanger",
        "piring", "gelas", "mangkok", "sendok", "garpu", "panci", "wajan",
        "teflon", "kompor", "kompor gas", "tumbler", "botol minum",
        "kotak makan", "lunchbox", "toples", "tanaman", "pot", "vas",
        "dekorasi", "wallpaper", "stiker dinding", "sofa", "lantai",
    ],
    "kecantikan": [
        "lipstik", "lip", "lip tint", "lip cream", "serum", "toner", "moisturizer",
        "sunscreen", "sunblock", "facial wash", "sabun muka", "masker", "cushion",
        "foundation", "bedak", "maskara", "eyeliner", "eyeshadow", "blush",
        "parfum", "perfume", "body lotion", "body wash", "shampoo", "sampo",
        "conditioner", "hair", "skincare", "makeup", "make up", "cream",
        "krim", "sikat gigi", "pasta gigi", "deodoran", "kutek", "gunting kuku",
    ],
    "makanan & minuman": [
        "makanan", "minuman", "snack", "keripik", "kue", "cokelat", "coklat",
        "kopi", "teh", "susu", "madu", "sambal", "bumbu", "minyak goreng",
        "tepung", "beras", "gula", "mie", "frozen", "daging", "ayam", "ikan",
        "udang", "sosis", "nugget", "beef", "wagyu", "sayur", "buah",
    ],
    "ibu & bayi": [
        "bayi", "baby", "popok", "diapers", "botol susu", "dot", "stroller",
        "gendongan", "mainan anak", "mainan", "baju anak", "sepatu anak",
        "ibu hamil", "menyusui",
    ],
    "otomotif": [
        "mobil", "motor", "helm", "oli", "ban", "velg", "spion", "jok",
        "knalpot", "aki", "busi", "kampas rem", "wiper", "cover mobil",
        "sarung jok", "parfum mobil",
    ],
    "hewan peliharaan": [
        "kucing", "anjing", "dog", "cat food", "dog food", "raw food",
        "pakan", "kandang", "pasir kucing", "aquarium", "akuarium", "ikan hias",
        "burung",
    ],
    "buku & alat tulis": [
        "buku", "novel", "kertas", "pulpen", "pensil", "spidol", "penghapus",
        "binder", "map", "stapler", "hvs", "sticky notes", "komik", "alat tulis",
    ],
}

# Tema keluhan untuk lapisan diagnostik. Pendekatannya berbasis aturan, bukan
# model black box, supaya hasilnya bisa ditelusuri dan dipertanggungjawabkan.
#
# Daftar ini disusun dari pembacaan sampel ulasan negatif asli, termasuk ejaan
# gaul ("tdk", "gak", "blm"). Kata yang juga muncul dalam pujian sengaja tidak
# dipakai sendirian — "gambar" akan cocok dengan "sesuai gambar".
_NEGASI = ["tidak", "tdk", "gak", "ga", "nggak", "ngga", "nga", "enggak", "gk"]


def _dengan_negasi(*kata: str) -> list[str]:
    return [f"{n} {k}" for n in _NEGASI for k in kata]


COMPLAINT_THEMES = {
    "Pengiriman": [
        "lama", "telat", "lambat", "belum sampai", "belum sampe", "blm sampai",
        "blm sampe", "baru sampai", "baru sampe", "ekspedisi", "kurir",
        "pengiriman", "resi", "hilang", "nyasar", "ongkir", "menunggu",
        *_dengan_negasi("sampai", "sampe", "nyampe"),
    ],
    "Kemasan": [
        "kemasan", "packing", "packaging", "bubble wrap", "penyok", "penyet",
        "bocor", "sobek", "kardus", "pecah", "remuk",
    ],
    "Tidak Berfungsi": [
        "mati", "error", "konslet", "korslet", "rusak total",
        "tidak bisa dipakai", "gak bisa dipake", "ga bisa dipake",
        *_dengan_negasi("bisa", "nyala", "jalan", "connect", "terdeteksi",
                        "berfungsi", "work"),
    ],
    "Kualitas Produk": [
        "jelek", "murahan", "tipis", "kualitas", "rusak", "cacat", "mudah rusak",
        "cepat rusak", "bahan", "kasar", "luntur", "kendor", "gampang rusak",
        "patah", "licin", "miring", "baterai", "batt", "cepat habis",
        "cepet abis", "cepat abis", "boros", *_dengan_negasi("awet", "kuat"),
    ],
    "Tidak Sesuai Deskripsi": [
        "beda", "berbeda", "salah kirim", "salah warna", "salah barang",
        "salah ukuran", "kekecilan", "kebesaran", "kecil", "kependekan",
        "kepanjangan", "tidak seperti gambar", "tidak lengkap", "tdk lengkap",
        "kurang lengkap", *_dengan_negasi("sesuai", "sama"),
    ],
    "Keaslian": [
        "palsu", "kw", "tiruan", "abal", "bukan ori", "bukan original",
        "imitasi", "bajakan", *_dengan_negasi("ori", "original", "asli"),
    ],
    "Pelayanan & Stok": [
        "penjual", "seller", "respon", "respons", "balas", "chat", "admin",
        "dicuekin", "komplain", "pelayanan", "kosong", "stok habis",
        "cancel", "batal", "refund", "retur", "tukar", "konfirmasi",
        *_dengan_negasi("ramah", "dibalas", "direspon"),
    ],
}

NEGATIVE_RATING_MAX = 2  # ulasan bintang 1-2 dianggap keluhan
