"""Model sentimen: mendeteksi ulasan negatif dari teksnya saja.

Pasangan dari review_analysis. Aturan kata kunci *menjelaskan* keluhannya soal
apa, tapi dirancang untuk ulasan yang sudah pasti negatif. Model ini *mendeteksi*
ulasan negatif dari teks, termasuk ejaan gaul dan kalimat tidak langsung yang
tidak pernah didaftarkan ("beli 3, cuma 1 yang bisa dipakai").

Konfigurasinya sama persis dengan model terbaik di notebook 03: TF-IDF + regresi
logistik dengan bobot kelas seimbang. Evaluasi memakai pemisahan per produk,
karena dengan pemisahan acak 42% produk muncul di data latih dan uji sekaligus.
Setelah dievaluasi, model dilatih ulang dengan semua data untuk dipakai
dashboard; angka evaluasi yang dilaporkan tetap dari data uji yang terpisah.
"""

import json

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline

from . import review_analysis
from .config import MODELS_DIR, SENTIMENT_METRICS, SENTIMENT_MODEL

# Batas bawaan. Notebook 03 menunjukkan batas ini bisa digeser untuk menukar
# precision dengan recall; 50% dipakai karena di situ F1 model sudah terbaik.
AMBANG_NEGATIF = 0.5


def buat_model() -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
        ("logreg", LogisticRegression(max_iter=3000, class_weight="balanced")),
    ])


def _skor(nama: str, y_asli: pd.Series, prediksi: np.ndarray) -> dict:
    return {
        "pendekatan": nama,
        "akurasi": float((prediksi == y_asli.values).mean()),
        "precision": float(precision_score(y_asli, prediksi, zero_division=0)),
        "recall": float(recall_score(y_asli, prediksi)),
        "f1": float(f1_score(y_asli, prediksi)),
    }


def pisah_per_produk(reviews: pd.DataFrame, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    """Indeks latih dan uji, dengan setiap produk hanya ada di salah satu sisi."""
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=seed)
    return next(gss.split(reviews, groups=reviews["produk_id"]))


def evaluasi(reviews: pd.DataFrame, seed: int = 42) -> dict:
    """Ukur model pada produk yang tidak pernah dilihatnya, dibanding dua pembanding."""
    X = reviews["ulasan"].astype(str)
    y = reviews["is_negatif"].astype(int)

    idx_latih, idx_uji = pisah_per_produk(reviews, seed)
    y_uji = y.iloc[idx_uji]

    model = buat_model().fit(X.iloc[idx_latih], y.iloc[idx_latih])
    proba = model.predict_proba(X.iloc[idx_uji])[:, 1]

    aturan = X.iloc[idx_uji].apply(lambda t: len(review_analysis.tandai_tema(t)) > 0)

    return {
        "ambang": AMBANG_NEGATIF,
        "jumlah_latih": int(len(idx_latih)),
        "jumlah_uji": int(len(idx_uji)),
        "negatif_uji": int(y_uji.sum()),
        "produk_uji": int(reviews["produk_id"].iloc[idx_uji].nunique()),
        "hasil": [
            _skor("Baseline: selalu 'bukan negatif'", y_uji, np.zeros(len(y_uji), dtype=int)),
            _skor("Aturan kata kunci", y_uji, aturan.astype(int).values),
            _skor("Model (TF-IDF + regresi logistik)", y_uji,
                  (proba >= AMBANG_NEGATIF).astype(int)),
        ],
    }


def latih(reviews: pd.DataFrame) -> dict:
    metrik = evaluasi(reviews)

    model = buat_model().fit(reviews["ulasan"].astype(str), reviews["is_negatif"].astype(int))
    metrik["jumlah_latih_final"] = int(len(reviews))
    # Model tersimpan dengan pickle, yang tidak dijamin terbaca oleh versi
    # scikit-learn lain. Versinya dicatat supaya dashboard bisa memperingatkan.
    metrik["versi_sklearn"] = sklearn.__version__

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, SENTIMENT_MODEL)
    SENTIMENT_METRICS.write_text(json.dumps(metrik, indent=2, ensure_ascii=False), encoding="utf-8")

    hasil_model = metrik["hasil"][-1]
    print(f"[model] diuji pada {metrik['jumlah_uji']:,} ulasan dari {metrik['produk_uji']:,} "
          f"produk yang tidak ikut dilatih")
    print(f"[model] precision {hasil_model['precision']:.1%}, recall {hasil_model['recall']:.1%}, "
          f"F1 {hasil_model['f1']:.1%} untuk kelas negatif")
    print(f"[model] tersimpan di {SENTIMENT_MODEL}")
    return metrik


def muat() -> tuple[Pipeline, dict]:
    metrik = json.loads(SENTIMENT_METRICS.read_text(encoding="utf-8"))
    return joblib.load(SENTIMENT_MODEL), metrik


def jelaskan(model: Pipeline, teks: str, nama_fitur: np.ndarray, top_n: int = 8) -> tuple[float, pd.DataFrame]:
    """Probabilitas negatif, plus kata dalam teks yang paling menggeser keputusan.

    Kontribusi tiap kata = bobot TF-IDF-nya di teks ini x koefisien model.
    Positif mendorong ke negatif, negatif mendorong ke bukan negatif. Untuk
    regresi logistik, jumlah semua kontribusi ditambah intersep persis sama
    dengan nilai yang dihitung model sebelum diubah jadi probabilitas, jadi
    penjelasannya bukan perkiraan.
    """
    vektor = model.named_steps["tfidf"].transform([teks])
    koef = model.named_steps["logreg"].coef_[0]
    proba = float(model.named_steps["logreg"].predict_proba(vektor)[0, 1])

    kontribusi = pd.DataFrame({
        "kata": nama_fitur[vektor.indices],
        "kontribusi": vektor.data * koef[vektor.indices],
    })
    kontribusi = (
        kontribusi.reindex(kontribusi["kontribusi"].abs().sort_values(ascending=False).index)
        .head(top_n)
        .reset_index(drop=True)
    )
    return proba, kontribusi
