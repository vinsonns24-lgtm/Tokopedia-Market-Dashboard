import json

import altair as alt
import joblib
import pandas as pd
import streamlit as st

from src.tampilan import HIJAU, ORANYE, angka, desimal, kartu_kpi, latar_putih, persen
from src.tema import TEMA, tandai_tema
from src.teks import bersihkan_teks

MIN_NEGATIF = 30


@st.cache_data
def muat_ulasan():
    df = pd.read_csv("Dataset/processed/ulasan_bersih.csv")
    df["teks_bersih"] = df["teks_bersih"].fillna("")
    return pd.concat([df, tandai_tema(df["teks_bersih"])], axis=1)


@st.cache_resource
def muat_model():
    return joblib.load("models/sentimen.joblib")


@st.cache_data
def muat_metrik():
    with open("models/sentimen_metrik.json", encoding="utf-8") as f:
        return json.load(f)


df = muat_ulasan()
metrik = muat_metrik()

st.title("Analisis Ulasan")
st.caption(
    "Ulasan pembeli Tokopedia tahun 2019 dari sekelompok kecil toko. Negatif = bintang 1 dan 2, "
    "positif = bintang 4 dan 5. Ulasan bintang 3 tidak diikutkan."
)

utama, panel = st.columns([3.3, 1], gap="large")

# ------------------------------------------------------------------ Panel kanan
with panel:
    with st.container(key="kartu-filter"):
        st.subheader("Filter")
        pilihan_kategori = st.multiselect(
            "Kategori",
            options=sorted(df["kategori"].unique()),
            placeholder="Semua kategori",
        )
        data = df[df["kategori"].isin(pilihan_kategori)] if pilihan_kategori else df
        st.caption(
            f"{angka(len(data))} dari {angka(len(df))} ulasan sesuai filter. "
            "Filter tidak berlaku untuk tab Coba Model."
        )

    with st.container(key="kartu-model"):
        st.subheader("Kinerja model sentimen")
        st.caption(f"Diuji dengan {angka(metrik['data_uji'])} ulasan dari produk yang tidak pernah dilihat saat latihan.")
        k1, k2 = st.columns(2)
        k1.metric("Precision", persen(metrik["uji_precision_negatif"]))
        k2.metric("Recall", persen(metrik["uji_recall_negatif"]))
        k3, k4 = st.columns(2)
        k3.metric("F1 negatif", desimal(metrik["uji_f1_negatif"]))
        k4.metric("Akurasi", persen(metrik["uji_akurasi"], 1))
        with st.expander("Cara membaca angka ini"):
            st.markdown(
                """
- Precision: dari ulasan yang ditebak negatif, berapa persen yang benar-benar negatif.
- Recall: dari semua ulasan negatif, berapa persen yang berhasil ditemukan.
- Akurasi terlihat tinggi karena 97,6% ulasan memang positif. Model yang selalu menebak positif pun mendapat akurasi 97,6%, tetapi tidak pernah menemukan keluhan. Karena itu ukuran utamanya adalah F1 untuk kelas negatif.

Keterbatasan: label berasal dari rating, dan cukup banyak ulasan bintang 4-5 yang isinya keluhan, sehingga precision di atas kemungkinan lebih rendah dari kenyataan. Model juga sering melewatkan keluhan yang pendek atau memakai kata yang jarang. Data latih berasal dari tahun 2019 dengan ulasan negatif yang didominasi kategori handphone. Proses lengkapnya ada di notebook `06_model_sentimen.ipynb`.
"""
            )

# ------------------------------------------------------------------ Area utama
negatif = data[data["label"] == "negatif"]
positif = data[data["label"] == "positif"]

with utama:
    kolom1, kolom2, kolom3, kolom4 = st.columns(4)
    with kolom1:
        kartu_kpi("Ulasan negatif", persen(len(negatif) / len(data), 1), f"{angka(len(negatif))} ulasan bintang 1-2", sorot=True)
    with kolom2:
        kartu_kpi("Jumlah ulasan", angka(len(data)), "setelah dibersihkan")
    with kolom3:
        kartu_kpi("Jumlah produk", angka(data["id_produk"].nunique()), "produk yang diulas")
    with kolom4:
        kartu_kpi("Jumlah toko", angka(data["id_toko"].nunique()), "toko penjual")

    st.write("")

    with st.container(key="kartu-analisis"):
        tab_kategori, tab_tema, tab_model = st.tabs(
            ["Keluhan per Kategori", "Tema Keluhan", "Coba Model Sentimen"]
        )

        # ---------------------------------------------------------- Tab kategori
        with tab_kategori:
            st.subheader("Persentase ulasan negatif per kategori")
            per_kategori = (
                data.groupby("kategori")
                .agg(jumlah_ulasan=("label", "size"), jumlah_negatif=("label", lambda s: (s == "negatif").sum()))
                .reset_index()
            )
            per_kategori["persen_negatif"] = per_kategori["jumlah_negatif"] / per_kategori["jumlah_ulasan"] * 100

            grafik = (
                alt.Chart(per_kategori)
                .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4, color=HIJAU)
                .encode(
                    y=alt.Y("kategori:N", title=None, sort="-x"),
                    x=alt.X("persen_negatif:Q", title="Ulasan negatif (%)"),
                    tooltip=[
                        alt.Tooltip("kategori:N", title="Kategori"),
                        alt.Tooltip("persen_negatif:Q", title="Ulasan negatif (%)", format=".1f"),
                        alt.Tooltip("jumlah_negatif:Q", title="Jumlah negatif", format=","),
                        alt.Tooltip("jumlah_ulasan:Q", title="Jumlah ulasan", format=","),
                    ],
                )
            )
            st.altair_chart(latar_putih(grafik), width="stretch")
            st.caption(
                "Handphone paling sering dikeluhkan, tetapi 38% keluhannya berasal dari hanya dua produk "
                "(headset bluetooth S530 dan Nokia 130). Kategori ini juga berisi aksesoris gadget, bukan hanya ponsel."
            )

            st.subheader("Produk yang paling banyak dikeluhkan")
            per_produk = (
                data.groupby("id_produk")
                .agg(
                    nama_produk=("nama_produk", "first"),
                    kategori=("kategori", "first"),
                    jumlah_ulasan=("label", "size"),
                    persen_negatif=("label", lambda s: (s == "negatif").mean() * 100),
                )
            )
            per_produk = per_produk[per_produk["jumlah_ulasan"] >= 20].sort_values("persen_negatif", ascending=False)
            if per_produk.empty:
                st.info("Tidak ada produk dengan minimal 20 ulasan untuk filter ini.")
            else:
                st.dataframe(
                    per_produk.head(10).reset_index(drop=True).style.format({"persen_negatif": lambda v: persen(v / 100, 1)}),
                    width="stretch",
                )
                st.caption("Hanya produk dengan minimal 20 ulasan, supaya persentasenya tidak berasal dari segelintir ulasan.")

        # ---------------------------------------------------------- Tab tema
        with tab_tema:
            daftar_tema = list(TEMA)
            st.subheader("Seberapa sering setiap tema disebut")

            if len(negatif) == 0:
                st.info("Tidak ada ulasan negatif untuk filter ini.")
            else:
                tema_label = pd.DataFrame({
                    "tema": daftar_tema,
                    "negatif": negatif[daftar_tema].mean().values * 100,
                    "positif": positif[daftar_tema].mean().values * 100,
                })
                tema_label["rasio"] = tema_label["negatif"] / tema_label["positif"]
                urutan_tema = tema_label.sort_values("rasio", ascending=False)["tema"].tolist()
                tema_panjang = tema_label.melt(id_vars=["tema", "rasio"], var_name="label", value_name="persen")

                grafik_tema = (
                    alt.Chart(tema_panjang)
                    .mark_bar(cornerRadiusTopRight=3, cornerRadiusBottomRight=3)
                    .encode(
                        y=alt.Y("tema:N", title=None, sort=urutan_tema),
                        yOffset=alt.YOffset("label:N", sort=["negatif", "positif"]),
                        x=alt.X("persen:Q", title="Persen ulasan yang menyebut tema"),
                        color=alt.Color(
                            "label:N",
                            scale=alt.Scale(domain=["negatif", "positif"], range=[ORANYE, HIJAU]),
                            legend=alt.Legend(title="Ulasan", orient="bottom"),
                        ),
                        tooltip=[
                            alt.Tooltip("tema:N", title="Tema"),
                            alt.Tooltip("label:N", title="Ulasan"),
                            alt.Tooltip("persen:Q", title="Persen", format=".1f"),
                        ],
                    )
                )
                st.altair_chart(latar_putih(grafik_tema), width="stretch")
                st.caption(
                    "Tema diurutkan dari yang paling khas untuk ulasan negatif. Kalau batang oranye lebih panjang "
                    "dari batang hijau, tema itu cenderung menjadi sumber keluhan. Kualitas produk adalah sumber keluhan "
                    "terbesar, sedangkan pengiriman dan pelayanan penjual lebih sering dipuji."
                )

                st.subheader("Tema yang disebut dalam ulasan negatif, per kategori")
                keluhan = negatif.groupby("kategori")[daftar_tema].mean() * 100
                keluhan_panjang = keluhan.reset_index().melt(id_vars="kategori", var_name="tema", value_name="persen")
                dasar = alt.Chart(keluhan_panjang).encode(
                    x=alt.X("tema:N", title=None, sort=daftar_tema, axis=alt.Axis(labelAngle=-20)),
                    y=alt.Y("kategori:N", title=None),
                )
                kotak = dasar.mark_rect(cornerRadius=4).encode(
                    color=alt.Color(
                        "persen:Q",
                        scale=alt.Scale(domain=[0, 50], range=["#fdf1ea", ORANYE]),
                        legend=alt.Legend(title="% ulasan negatif"),
                    ),
                    tooltip=[
                        alt.Tooltip("kategori:N", title="Kategori"),
                        alt.Tooltip("tema:N", title="Tema"),
                        alt.Tooltip("persen:Q", title="Persen", format=".0f"),
                    ],
                )
                label = dasar.mark_text(fontSize=12, color="#0b0b0b").encode(text=alt.Text("persen:Q", format=".0f"))
                st.altair_chart(latar_putih(kotak + label), width="stretch")

                jumlah_neg = negatif["kategori"].value_counts()
                sedikit = jumlah_neg[jumlah_neg < MIN_NEGATIF]
                if not sedikit.empty:
                    st.caption(
                        "Kategori dengan kurang dari 30 ulasan negatif, sehingga persentasenya kurang stabil: "
                        + ", ".join(f"{k} ({v})" for k, v in sedikit.items())
                    )

                st.subheader("Contoh ulasan negatif")
                pilihan_tema = st.selectbox("Tema", daftar_tema, index=daftar_tema.index("Kualitas produk"))
                contoh = negatif[negatif[pilihan_tema]]
                if contoh.empty:
                    st.info("Tidak ada ulasan negatif dengan tema ini untuk filter yang dipilih.")
                else:
                    st.dataframe(
                        contoh[["kategori", "rating", "teks"]].sample(min(10, len(contoh)), random_state=1),
                        width="stretch",
                        hide_index=True,
                    )

        # ---------------------------------------------------------- Tab model
        with tab_model:
            st.subheader("Coba model sentimen")
            st.caption(
                "Tulis ulasan dalam bahasa Indonesia, lalu model akan menebak apakah ulasan itu positif atau negatif. "
                "Teks dibersihkan dulu dengan cara yang sama seperti saat model dilatih, termasuk mengubah singkatan "
                "seperti \"gk\" menjadi \"tidak\"."
            )

            CONTOH = [
                "Barang sesuai pesanan, pengiriman cepat. Mantap gan!",
                "Brg gk sesuai gambar, kecewa bgt. Udah chat seller gk dibales",
                "Barang bagus tapi pengirimannya lama banget",
                "Baru dipakai 2 hari udah mati, minta retur",
            ]
            contoh_dipilih = st.selectbox("Pilih contoh atau tulis sendiri di bawah", CONTOH)
            teks = st.text_area("Teks ulasan", value=contoh_dipilih, height=100)

            if teks.strip():
                model = muat_model()
                teks_bersih = bersihkan_teks(teks)

                if not teks_bersih:
                    st.warning("Setelah dibersihkan, teks ini kosong. Coba tulis ulasan dengan kata-kata, bukan hanya emoji atau angka.")
                else:
                    masukan = pd.Series([teks_bersih])
                    kolom_negatif = list(model.classes_).index("negatif")
                    peluang_negatif = model.predict_proba(masukan)[0, kolom_negatif]
                    tebakan = model.predict(masukan)[0]

                    kiri, kanan = st.columns(2)
                    with kiri:
                        kartu_kpi("Tebakan model", tebakan.capitalize(), "positif atau negatif", sorot=tebakan == "positif")
                    with kanan:
                        kartu_kpi("Peluang negatif", persen(peluang_negatif),
                                  f"ditebak negatif mulai {persen(metrik['ambang_peluang_negatif'])}")
                    st.write("")
                    st.progress(float(peluang_negatif))
                    st.caption(
                        f"Teks yang dibaca model: \"{teks_bersih}\". Ambang {persen(metrik['ambang_peluang_negatif'])} "
                        "sengaja rendah karena ulasan negatif sangat jarang di data latih."
                    )

            st.caption(
                "Keterbatasan: model membaca kata dan pasangan dua kata, bukan susunan kalimat. Kalimat seperti "
                "\"tidak jelek\" bisa salah ditebak, dan ulasan campuran seperti \"bagus tapi lama\" cenderung ditebak positif."
            )
