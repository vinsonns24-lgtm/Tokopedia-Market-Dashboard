"""Product Intelligence Dashboard — analisis peluang jualan di Tokopedia.

Tiga lapis, mengikuti alur pertanyaan seorang calon penjual:
  1. Ringkasan  — kategori ini menarik atau tidak?
  2. Peluang    — di segmen harga mana celahnya?
  3. Diagnostik — apa yang bisa saya lakukan lebih baik dari pesaing?

Ditambah satu alat: Cek Ulasan, yang memakai model sentimen untuk menilai
ulasan baru yang ditempel pengguna.
"""

import sqlite3

import pandas as pd
import plotly.graph_objects as go
import sklearn
import streamlit as st

from src import review_analysis, sentiment_model

DB_PATH = "database.db"

# Palet dari panduan visualisasi, dipakai apa adanya beserta batasannya:
# untuk scatter hanya tiga slot pertama yang lolos uji keterbacaan buta warna.
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]
SEQ_BLUE = [
    [0.0, "#cde2fb"], [0.25, "#86b6ef"], [0.5, "#3987e5"],
    [0.75, "#256abf"], [1.0, "#0d366b"],
]
# Untuk titik scatter, langkah paling terang dinaikkan supaya tiap titik tetap
# terlihat di atas latar terang — beda dengan heatmap yang boleh memudar ke
# permukaan karena selnya bersebelahan dan tepinya sudah membentuk batas.
SEQ_BLUE_MARKS = [
    [0.0, "#86b6ef"], [0.33, "#3987e5"], [0.66, "#256abf"], [1.0, "#0d366b"],
]
# Skor peluang bertanda (positif = ada celah, negatif = sesak), jadi skalanya
# divergen dengan abu-abu netral di titik nol.
DIVERGING = [[0.0, "#e34948"], [0.5, "#f0efec"], [1.0, "#2a78d6"]]

st.set_page_config(page_title="Product Intelligence Dashboard", layout="wide")


@st.cache_data
def muat(nama_tabel: str) -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql(f"SELECT * FROM {nama_tabel}", conn)


def rapikan(fig: go.Figure, tinggi: int = 380) -> go.Figure:
    """Terapkan chrome yang sama ke semua grafik: grid tipis, teks pakai tinta."""
    fig.update_layout(
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif",
                  color=INK_2, size=13),
        margin=dict(l=8, r=8, t=8, b=8),
        height=tinggi,
        hoverlabel=dict(bgcolor=SURFACE, bordercolor=AXIS,
                        font=dict(color=INK, size=12)),
    )
    fig.update_xaxes(gridcolor=GRID, linecolor=AXIS, zerolinecolor=AXIS,
                     tickfont=dict(color=MUTED), title_font=dict(color=INK_2))
    fig.update_yaxes(gridcolor=GRID, linecolor=AXIS, zerolinecolor=AXIS,
                     tickfont=dict(color=MUTED), title_font=dict(color=INK_2))
    return fig


@st.cache_resource
def model_sentimen():
    model, metrik = sentiment_model.muat()
    nama_fitur = model.named_steps["tfidf"].get_feature_names_out()
    return model, metrik, nama_fitur


def rupiah(nilai: float) -> str:
    if pd.isna(nilai):
        return "-"
    if nilai >= 1_000_000_000_000:
        return f"Rp{nilai / 1_000_000_000_000:.1f} T"
    if nilai >= 1_000_000_000:
        return f"Rp{nilai / 1_000_000_000:.1f} M"
    if nilai >= 1_000_000:
        return f"Rp{nilai / 1_000_000:.1f} jt"
    if nilai >= 1_000:
        return f"Rp{nilai / 1_000:.0f} rb"
    return f"Rp{nilai:,.0f}"


try:
    listings = muat("listings_segmented")
    segmen = muat("segment_summary")
    stabilitas = muat("segment_stability")
    kategori_ringkas = muat("category_summary")
    reviews = muat("reviews")
    tema = muat("complaint_themes")
    kata_kunci = muat("keywords_negatif")
except Exception as exc:
    st.error(
        f"Database belum siap ({exc}).\n\n"
        "Jalankan dulu `python run_pipeline.py` setelah menaruh kedua CSV di `data/raw/`."
    )
    st.stop()

st.title("Product Intelligence Dashboard")
st.caption(
    "Analisis peluang berjualan di Tokopedia berdasarkan "
    f"{len(listings):,} listing produk dan {len(reviews):,} ulasan pembeli."
)

with st.sidebar:
    st.header("Filter")
    daftar_kategori = sorted(listings["kategori"].unique())
    pilih_kategori = st.multiselect(
        "Kategori", daftar_kategori,
        default=[k for k in daftar_kategori if k != "lainnya"],
    )
    sembunyikan_lainnya = st.checkbox(
        "Sembunyikan produk tak terklasifikasi", value=True,
        help="Produk yang nama-nya tidak cocok dengan kata kunci kategori mana pun.",
    )

kerja = listings[listings["kategori"].isin(pilih_kategori)] if pilih_kategori else listings
if sembunyikan_lainnya:
    kerja = kerja[kerja["kategori"] != "lainnya"]

if kerja.empty:
    st.warning("Tidak ada data untuk filter yang dipilih.")
    st.stop()

tab1, tab2, tab3, tab_cek, tab4 = st.tabs(
    ["Ringkasan Pasar", "Peluang Segmen", "Diagnostik Ulasan", "Cek Ulasan", "Metodologi"]
)

# ---------------------------------------------------------------- Lapis 1
with tab1:
    st.subheader("Kategori ini menarik atau tidak?")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Produk", f"{len(kerja):,}")
    k2.metric("Penjual", f"{kerja['nama_toko'].nunique():,}")
    k3.metric("Estimasi nilai pasar", rupiah(kerja["estimasi_omzet"].sum()))
    k4.metric("Harga median", rupiah(kerja["harga"].median()))

    st.caption(
        "Estimasi nilai pasar dihitung dari harga dikali perkiraan jumlah terjual, "
        "dengan nilai per produk dipangkas di persentil 99,5 tiap kategori agar "
        "listing janggal tidak mendominasi. Jakarta digabung karena banyak toko "
        "hanya menulis \"Jakarta\" tanpa kota administrasinya."
    )

    kiri, kanan = st.columns(2)

    with kiri:
        st.markdown("**Nilai pasar per kategori**")
        data = (
            kerja.groupby("kategori")["estimasi_omzet"].sum()
            .sort_values().reset_index()
        )
        fig = go.Figure(go.Bar(
            x=data["estimasi_omzet"] / 1e9, y=data["kategori"], orientation="h",
            marker=dict(color=SERIES[0], cornerradius=4),
            hovertemplate="<b>%{y}</b><br>Nilai pasar: %{customdata}<extra></extra>",
            customdata=[rupiah(v) for v in data["estimasi_omzet"]],
        ))
        fig.update_layout(showlegend=False)
        fig.update_xaxes(title="Estimasi nilai pasar (Rp miliar)", tickformat=",.0f")
        st.plotly_chart(rapikan(fig, 340), width="stretch")

    with kanan:
        st.markdown("**10 kota dengan penjual terbanyak**")
        data = (
            kerja[kerja["wilayah"] != "Tidak Diketahui"]
            .groupby("wilayah")["nama_toko"].nunique()
            .sort_values(ascending=False).head(10)
            .sort_values().reset_index()
        )
        fig = go.Figure(go.Bar(
            x=data["nama_toko"], y=data["wilayah"], orientation="h",
            marker=dict(color=SERIES[2], cornerradius=4),
            hovertemplate="<b>%{y}</b><br>%{x:,} penjual<extra></extra>",
        ))
        fig.update_layout(showlegend=False)
        fig.update_xaxes(title="Jumlah penjual unik")
        st.plotly_chart(rapikan(fig, 340), width="stretch")

    st.markdown("**Ringkasan per kategori**")
    tampil = kategori_ringkas[kategori_ringkas["kategori"].isin(kerja["kategori"].unique())].copy()
    tampil["median_harga"] = tampil["median_harga"].apply(rupiah)
    tampil["total_omzet"] = tampil["total_omzet"].apply(rupiah)
    tampil["omzet_per_produk"] = tampil["omzet_per_produk"].apply(rupiah)
    st.dataframe(
        tampil.rename(columns={
            "kategori": "Kategori", "jumlah_produk": "Produk",
            "jumlah_penjual": "Penjual", "median_harga": "Harga median",
            "total_terjual": "Total terjual", "total_omzet": "Nilai pasar",
            "median_rating": "Rating median", "median_diskon": "Diskon median (%)",
            "omzet_per_produk": "Nilai per produk",
        }),
        width="stretch", hide_index=True,
    )

# ---------------------------------------------------------------- Lapis 2
with tab2:
    st.subheader("Di segmen harga mana celahnya?")
    st.markdown(
        "Skor peluang menggabungkan tiga hal: **nilai penjualan besar**, "
        "**pesaing sedikit**, dan **banyak pesaing yang mengecewakan pembeli** "
        "(rating di bawah 4,7). Biru berarti ada ruang masuk, merah berarti "
        "segmen sudah sesak atau pesaingnya kuat."
    )
    st.caption(
        "Segmen harga dihitung per kategori: Ekonomis adalah 25% produk termurah "
        "di kategori itu, Super Premium 25% termahal."
    )

    seg = segmen[segmen["kategori"].isin(kerja["kategori"].unique())]
    if seg.empty:
        st.info("Tidak ada data segmen untuk filter ini.")
    else:
        urutan = ["Ekonomis", "Menengah", "Premium", "Super Premium"]
        pivot = (
            seg.pivot(index="kategori", columns="segmen_harga", values="skor_peluang")
            .reindex(columns=[u for u in urutan if u in seg["segmen_harga"].unique()])
        )
        batas = float(max(abs(seg["skor_peluang"].min()), abs(seg["skor_peluang"].max()), 1))

        fig = go.Figure(go.Heatmap(
            z=pivot.values, x=pivot.columns, y=pivot.index,
            colorscale=DIVERGING, zmid=0, zmin=-batas, zmax=batas,
            xgap=2, ygap=2,
            colorbar=dict(title="Skor", outlinewidth=0, tickfont=dict(color=MUTED)),
            hovertemplate="<b>%{y}</b> — %{x}<br>Skor peluang: %{z:.2f}<extra></extra>",
        ))
        st.plotly_chart(rapikan(fig, 80 + 34 * len(pivot)), width="stretch")

        st.markdown("**Lima segmen dengan peluang terbaik**")
        top = seg.nlargest(5, "skor_peluang").merge(
            stabilitas[["kategori", "segmen_harga", "porsi_top5"]],
            on=["kategori", "segmen_harga"], how="left",
        )
        top["median_harga"] = top["median_harga"].apply(rupiah)
        top["omzet_per_produk"] = top["omzet_per_produk"].apply(rupiah)
        top["porsi_pesaing_lemah"] = (top["porsi_pesaing_lemah"] * 100).round(1)
        top["porsi_top5"] = (top["porsi_top5"] * 100).round(0)
        st.dataframe(
            top[[
                "kategori", "segmen_harga", "skor_peluang", "porsi_top5", "jumlah_produk",
                "median_harga", "omzet_per_produk", "porsi_pesaing_lemah",
            ]].rename(columns={
                "kategori": "Kategori", "segmen_harga": "Segmen",
                "skor_peluang": "Skor peluang",
                "porsi_top5": "Bertahan di 5 besar (%)",
                "jumlah_produk": "Produk pesaing",
                "median_harga": "Harga median",
                "omzet_per_produk": "Nilai penjualan per produk",
                "porsi_pesaing_lemah": "Pesaing lemah (%)",
            }),
            width="stretch", hide_index=True,
        )
        st.caption(
            "**Bertahan di 5 besar**: dari 300 sampel ulang produk (bootstrap), berapa "
            "persen yang tetap menempatkan segmen ini di 5 besar dari semua kategori, "
            "apa pun filter yang dipilih. Angka rendah berarti "
            "peringkatnya bisa berubah hanya karena produk yang kebetulan ter-scrape "
            "sedikit berbeda, jadi baca urutannya sebagai kandidat setara, bukan "
            "peringkat pasti. Rincian uji ada di notebook 04."
        )
        st.caption(
            "Yang paling menentukan papan atas adalah pesaing yang sedikit dan pesaing "
            "yang lemah. Sebagian besar segmen teratas justru punya nilai penjualan di "
            "bawah rata-rata, jadi skor ini menunjuk pasar yang sepi dan kurang "
            "terlayani, belum tentu pasar yang besar."
        )

    st.divider()
    st.markdown("**Sebaran harga dan penjualan**")
    fokus = st.selectbox(
        "Pilih satu kategori untuk ditelusuri",
        sorted(kerja["kategori"].unique()),
        help="Ditampilkan satu kategori agar warna bisa dipakai untuk rating.",
    )
    detail = kerja[(kerja["kategori"] == fokus) & (kerja["terjual"] > 0)].copy()

    if detail.empty:
        st.info("Tidak ada produk dengan penjualan tercatat di kategori ini.")
    else:
        contoh = detail.sample(min(3000, len(detail)), random_state=42)
        fig = go.Figure(go.Scatter(
            x=contoh["harga"], y=contoh["terjual"], mode="markers",
            marker=dict(
                size=9, color=contoh["rating"], colorscale=SEQ_BLUE_MARKS,
                cmin=1, cmax=5, line=dict(color=SURFACE, width=2),
                colorbar=dict(title="Rating", outlinewidth=0,
                              tickfont=dict(color=MUTED)),
            ),
            text=contoh["nama_produk"].str.slice(0, 70),
            hovertemplate=("<b>%{text}</b><br>Harga: %{x:,.0f}<br>"
                           "Terjual: %{y:,.0f}<br>Rating: %{marker.color:.1f}<extra></extra>"),
        ))
        # Label manual: format SI bawaan menulis "1M" untuk satu juta, padahal
        # dalam konvensi Indonesia "M" berarti miliar.
        fig.update_xaxes(
            type="log", title="Harga (Rp, skala log)",
            tickvals=[1e3, 1e4, 1e5, 1e6, 1e7, 1e8],
            ticktext=["1 rb", "10 rb", "100 rb", "1 jt", "10 jt", "100 jt"],
        )
        fig.update_yaxes(
            type="log", title="Perkiraan terjual (skala log)",
            tickvals=[1, 10, 100, 1e3, 1e4, 1e5],
            ticktext=["1", "10", "100", "1 rb", "10 rb", "100 rb"],
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(rapikan(fig, 420), width="stretch")
        st.caption(
            "Kedua sumbu memakai skala logaritma karena harga dan penjualan sangat "
            "timpang — sedikit produk terlaris menguasai hampir seluruh volume."
        )

# ---------------------------------------------------------------- Lapis 3
with tab3:
    st.subheader("Apa yang bisa saya lakukan lebih baik?")
    st.markdown(
        "Lapisan ini membaca ulasan bintang 1-2 dan mengelompokkan keluhannya. "
        "Keluhan yang sering muncul adalah titik lemah pesaing — dan peluang pembeda bagimu."
    )
    st.caption(
        "Data ulasan hanya mencakup lima kategori: handphone, elektronik, fashion, "
        "olahraga, dan pertukangan. Kategori lain di lapis 1-2 tidak punya data ulasan."
    )

    if tema.empty:
        st.info("Belum ada data tema keluhan.")
    else:
        kategori_ulasan = sorted(tema["kategori"].unique())
        pilih = st.selectbox("Kategori", kategori_ulasan)

        data = tema[tema["kategori"] == pilih].sort_values("porsi")
        n_negatif = int(data["total_negatif"].iloc[0]) if not data.empty else 0
        n_total = int((reviews["kategori"] == pilih).sum())
        st.markdown(
            f"Dasar analisis: **{n_negatif:,} ulasan negatif** dari {n_total:,} "
            f"ulasan di kategori {pilih}. Satu ulasan bisa menyinggung lebih dari "
            "satu tema, jadi porsinya tidak berjumlah 100%."
        )
        if n_negatif < 50:
            st.warning(
                f"Hanya {n_negatif} ulasan negatif di kategori ini — terlalu sedikit "
                "untuk disimpulkan. Anggap sebagai gambaran kasar."
            )

        kiri, kanan = st.columns([3, 2])

        with kiri:
            st.markdown(f"**Keluhan utama di kategori {pilih}**")
            fig = go.Figure(go.Bar(
                x=data["porsi"] * 100, y=data["tema"], orientation="h",
                marker=dict(color=SERIES[1], cornerradius=4),
                text=[f"{p * 100:.0f}%" for p in data["porsi"]],
                textposition="outside", textfont=dict(color=INK_2),
                hovertemplate=("<b>%{y}</b><br>%{x:.1f}% dari ulasan negatif"
                               "<br>%{customdata:,} ulasan<extra></extra>"),
                customdata=data["jumlah"],
            ))
            fig.update_layout(showlegend=False)
            fig.update_xaxes(title="Porsi dari ulasan negatif (%)", range=[0, 100])
            st.plotly_chart(rapikan(fig, 340), width="stretch")

        with kanan:
            st.markdown("**Kata paling menonjol**")
            kk = kata_kunci[kata_kunci["kategori"] == pilih].head(10).sort_values("skor")
            if kk.empty:
                st.info("Tidak ada kata menonjol.")
            else:
                fig = go.Figure(go.Bar(
                    x=kk["skor"], y=kk["kata"], orientation="h",
                    marker=dict(color=SERIES[2], cornerradius=4),
                    hovertemplate="<b>%{y}</b><br>Skor TF-IDF: %{x:.3f}<extra></extra>",
                ))
                fig.update_layout(showlegend=False)
                fig.update_xaxes(title="Skor TF-IDF")
                st.plotly_chart(rapikan(fig, 340), width="stretch")

        st.markdown("**Perbandingan antar kategori**")
        pivot = tema.pivot(index="kategori", columns="tema", values="porsi").fillna(0) * 100
        fig = go.Figure(go.Heatmap(
            z=pivot.values, x=pivot.columns, y=pivot.index,
            colorscale=SEQ_BLUE, xgap=2, ygap=2,
            colorbar=dict(title="%", outlinewidth=0, tickfont=dict(color=MUTED)),
            hovertemplate="<b>%{y}</b> — %{x}<br>%{z:.1f}% ulasan negatif<extra></extra>",
        ))
        st.plotly_chart(rapikan(fig, 300), width="stretch")

        with st.expander("Lihat contoh ulasan negatif"):
            contoh = reviews[(reviews["kategori"] == pilih) & (reviews["is_negatif"] == 1)]
            if contoh.empty:
                st.write("Tidak ada ulasan negatif di kategori ini.")
            else:
                st.dataframe(
                    contoh[["rating", "nama_produk", "ulasan"]]
                    .head(30).rename(columns={
                        "rating": "Rating", "nama_produk": "Produk", "ulasan": "Ulasan",
                    }),
                    width="stretch", hide_index=True,
                )

# ---------------------------------------------------------------- Cek Ulasan
# Contoh dipilih untuk memperlihatkan keempat kemungkinan hasil: model dan
# aturan sepakat, hanya model yang menangkap, hanya aturan yang terpancing,
# dan tidak ada keluhan.
CONTOH_ULASAN = {
    "Tulis sendiri": "",
    "Keluhan jelas": "Pengiriman lama banget, kemasan penyok dan barangnya rusak",
    "Keluhan tidak langsung": "Beli 3. Cuma 1 yang bisa dipakai",
    "Ejaan gaul": "Beli 5 tdk bs dipakai semua",
    "Kata keluhan dalam pujian": "Sudah lama langganan di toko ini, selalu puas",
    "Pujian biasa": "Barang sampai dengan cepat, sesuai deskripsi, mantap",
}

with tab_cek:
    st.subheader("Ulasan ini keluhan atau bukan?")
    st.markdown(
        "Tempel satu ulasan. **Model** menilai seberapa mungkin ulasan itu keluhan, "
        "lalu **aturan kata kunci** dari lapis Diagnostik menunjukkan keluhannya soal apa. "
        "Keduanya sengaja ditampilkan berdampingan: model lebih jeli mendeteksi, "
        "aturan lebih mudah dijelaskan."
    )

    try:
        model, metrik, nama_fitur = model_sentimen()
    except (FileNotFoundError, OSError):
        st.info("Model sentimen belum dilatih. Jalankan dulu `python run_pipeline.py`.")
    else:
        if metrik.get("versi_sklearn") != sklearn.__version__:
            st.warning(
                f"Model dilatih dengan scikit-learn {metrik.get('versi_sklearn')}, "
                f"sedangkan yang terpasang {sklearn.__version__}. Hasilnya bisa meleset; "
                "jalankan ulang pipeline untuk melatih model dengan versi yang sama."
            )

        pilih_contoh = st.selectbox("Mulai dari contoh", list(CONTOH_ULASAN))
        teks = st.text_area(
            "Teks ulasan", value=CONTOH_ULASAN[pilih_contoh], height=100,
            placeholder="Contoh: barang datang tapi tidak bisa nyala",
        ).strip()

        if teks:
            proba, kontribusi = sentiment_model.jelaskan(model, teks, nama_fitur)
            keluhan = proba >= metrik["ambang"]
            tema_cocok = review_analysis.tandai_tema(teks)

            k1, k2 = st.columns(2)
            k1.metric("Probabilitas keluhan (model)", f"{proba:.0%}")
            k2.metric("Tema keluhan (aturan)", ", ".join(tema_cocok) if tema_cocok else "Tidak ada")

            if keluhan and tema_cocok:
                st.markdown("Model dan aturan **sepakat**: ini keluhan, dan aturan bisa menjelaskan isinya.")
            elif keluhan:
                st.markdown(
                    "**Hanya model yang menangkap.** Tidak ada kata kunci yang cocok, jadi "
                    "keluhan seperti ini tidak ikut terhitung di lapis Diagnostik. Ini jenis "
                    "ulasan yang membuat sekitar 31% ulasan negatif tidak terklasifikasi."
                )
            elif tema_cocok:
                st.markdown(
                    "**Hanya aturan yang terpancing.** Ada kata yang terdaftar sebagai keluhan, "
                    "tapi model menilai ulasan ini bukan keluhan. Aturan dirancang untuk "
                    "*mengelompokkan* ulasan yang sudah pasti negatif, bukan untuk *mendeteksinya*. "
                    "Kata seperti \"lama\" juga muncul dalam pujian."
                )
            else:
                st.markdown("Tidak ada tanda keluhan, baik menurut model maupun aturan.")

            st.markdown("**Kata yang paling menggeser keputusan model**")
            if kontribusi.empty:
                st.info(
                    "Tidak ada kata dalam teks ini yang dikenal model, jadi probabilitasnya "
                    "hanya berasal dari titik awal model, bukan dari isi teks."
                )
            else:
                data = kontribusi.sort_values("kontribusi")
                fig = go.Figure(go.Bar(
                    x=data["kontribusi"], y=data["kata"], orientation="h",
                    marker=dict(
                        color=[SERIES[1] if v > 0 else SERIES[0] for v in data["kontribusi"]],
                        cornerradius=4,
                    ),
                    hovertemplate="<b>%{y}</b><br>Kontribusi: %{x:+.2f}<extra></extra>",
                ))
                fig.update_layout(showlegend=False)
                fig.update_xaxes(title="← ke bukan keluhan  ·  ke keluhan →")
                st.plotly_chart(rapikan(fig, 60 + 32 * len(data)), width="stretch")
                st.caption(
                    "Kontribusi = bobot kata di teks ini dikali koefisien model. "
                    "Untuk regresi logistik, penjumlahan inilah yang dihitung model, "
                    "jadi grafik ini bukan perkiraan; yang ditampilkan hanya delapan "
                    "kontribusi terbesar. Model membaca unigram dan bigram, "
                    "sehingga pasangan kata seperti \"tidak sesuai\" dihitung sendiri."
                )

        with st.expander("Seberapa bisa dipercaya model ini?"):
            st.markdown(
                f"Model diuji pada **{metrik['jumlah_uji']:,} ulasan dari "
                f"{metrik['produk_uji']:,} produk yang tidak pernah dilihatnya saat "
                f"latihan**, {metrik['negatif_uji']} di antaranya negatif. Data dipisah "
                "per produk, bukan per ulasan; dengan pemisahan acak, 42% produk akan "
                "muncul di data latih dan uji sekaligus, dan skornya menggelembung."
            )
            st.dataframe(
                pd.DataFrame(metrik["hasil"]).rename(columns={
                    "pendekatan": "Pendekatan", "akurasi": "Akurasi",
                    "precision": "Precision", "recall": "Recall", "f1": "F1",
                }).style.format({k: "{:.1%}" for k in ["Akurasi", "Precision", "Recall", "F1"]}),
                width="stretch", hide_index=True,
            )
            st.markdown(
                "Baris baseline menunjukkan kenapa akurasi tidak dipakai: menebak "
                f"\"bukan negatif\" untuk semua ulasan sudah {metrik['hasil'][0]['akurasi']:.1%} "
                "akurat, tapi tidak "
                "menemukan satu pun keluhan. Precision, recall, dan F1 di tabel dihitung "
                "untuk kelas negatif.\n\n"
                f"Setelah diuji, model dilatih ulang dengan seluruh "
                f"{metrik['jumlah_latih_final']:,} ulasan untuk dipakai di sini. "
                "Batasnya: data ulasan berasal dari 2019 dan hanya lima kategori, label "
                "diambil dari rating (bintang 1-2 = keluhan), dan batas keputusan 50%. "
                "Proses lengkapnya ada di notebook 03."
            )

# ---------------------------------------------------------------- Metodologi
with tab4:
    st.subheader("Metodologi dan keterbatasan")
    st.markdown(
        """
**Sumber data**

- *Indonesia E-Commerce Dataset: Tokopedia Listings* — 29.519 listing produk, lisensi Apache 2.0
- *Tokopedia Product Reviews* — 40.607 ulasan berbahasa Indonesia dari 3.664 produk

**Keputusan pengolahan**

1. **Kategori diturunkan dari nama produk.** Dataset listing tidak punya kolom
   kategori. Kata kunci dicocokkan sebagai **kata utuh** dan diberi bobot
   panjang, sehingga "sepatu bola" menang atas "sepatu". Versi awal memakai
   pencocokan potongan huruf, dan "mur" (pertukangan) ikut cocok dengan
   "murah" — kategori pertukangan menggelembung dari 440 menjadi 1.469 produk
   dan 9,5% produk salah kategori, tanpa satu pun pesan error. Lima kategori
   mengikuti dataset ulasan; tujuh lainnya ditambahkan karena dataset listing
   adalah marketplace umum. Sekitar 25% produk tetap tak terklasifikasi.

2. **Kolom terjual dan jumlah ulasan dikonversi dari teks.** "1rb+ terjual"
   menjadi 1000, "10 ulasan" menjadi 10. Hasilnya batas bawah, bukan angka pasti.

3. **Rating 0 dianggap kosong**, karena artinya produk belum pernah dinilai.

4. **Segmen harga memakai kuartil di dalam tiap kategori**, bukan kuartil global.
   Rentang harga antar kategori terlalu jauh berbeda untuk dibandingkan langsung.

5. **Skor peluang** = nilai penjualan − jumlah pesaing + porsi pesaing lemah,
   masing-masing dalam z-score. Dua pilihan yang disengaja:
   - Permintaan dalam **Rupiah, bukan unit**. Dengan unit, segmen termurah
     selalu menang karena barang murah laku lebih banyak.
   - Kepuasan diukur sebagai **porsi pesaing dengan rating di bawah 4,7**,
     bukan rating median. Rating median hampir semua segmen 4,9-5,0, sehingga
     selisihnya tidak bermakna.

   Skor ini **diuji kestabilannya** terhadap 13 variasi desain (ambang, bobot,
   log, persentil pemangkasan) dan 300 sampel ulang produk. Hanya dua segmen
   teratas yang kokoh; urutan di bawahnya mudah bergeser.

6. **Tema keluhan memakai aturan kata kunci, bukan model black box.** Setiap
   angka bisa ditelusuri ke kata pemicunya. Daftar kata disusun dari pembacaan
   sampel ulasan asli, termasuk ejaan gaul ("tdk sesuai", "blm sampe"). Kata
   yang juga muncul dalam pujian, seperti "gambar" pada "sesuai gambar",
   sengaja tidak dipakai sendirian.

7. **Tab Cek Ulasan memakai model, bukan aturan.** TF-IDF + regresi logistik
   dengan bobot kelas seimbang, dievaluasi pada produk yang tidak ikut
   dilatih. Model dipakai untuk *mendeteksi* keluhan; aturan tetap dipakai
   untuk *menjelaskan* isinya, karena lapis Diagnostik butuh angka yang bisa
   ditelusuri ke kata pemicunya.

**Keterbatasan yang perlu diketahui pembaca**

- Kedua dataset **tidak bisa digabung per produk** — tidak ada kunci yang sama
  dan periodenya berbeda (ulasan dari 2019, listing jauh lebih baru).
  Perbandingan hanya sah pada level kategori.
- **Rating sangat menggelembung**: median rating listing 5,0. Hanya 2,3% ulasan
  berbintang 1-2, sehingga lapis diagnostik bertumpu pada sekitar 900 ulasan.
- Sekitar **31% ulasan negatif tidak tertangkap tema apa pun**. Isinya campuran:
  kekecewaan umum ("kecewa", "parah"), pujian dengan bintang rendah, dan
  keluhan spesifik yang luput karena ejaan ("tdk bs dipakai") atau kalimat
  tidak langsung ("beli 3, cuma 1 yang bisa dipakai"). Yang terakhir adalah
  batas nyata pendekatan berbasis aturan.
- **Jumlah pesaing diukur dari sampel, bukan seluruh Tokopedia.** Kategori
  seperti otomotif (390 produk) tampak sepi pesaing, tapi bisa jadi karena
  jarang ter-scrape, bukan karena pasarnya sepi. Skor peluang teratas justru
  didominasi kategori kecil, jadi harus dikonfirmasi dengan data lain sebelum
  dijadikan keputusan.
- Perkiraan nilai pasar bersifat **batas bawah** karena keterbatasan kolom terjual.
- Data adalah potret satu waktu, bukan deret waktu, sehingga tren musiman
  tidak bisa dianalisis.

**Etika pengumpulan data**

Komponen scraping dalam project ini memeriksa `robots.txt` lebih dulu dan
berhenti bila aksesnya dilarang. Hasil pemeriksaan dicatat sebagai temuan,
bukan rintangan yang diakali.
        """
    )
