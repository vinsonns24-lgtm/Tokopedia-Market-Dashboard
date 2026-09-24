import altair as alt
import pandas as pd
import streamlit as st

from src.tampilan import ABU, HIJAU, ORANYE, angka, batang_horizontal, kartu_kpi, latar_putih, persen, rupiah

KATA_KUNCI = {
    "premium": r"\bpremium\b",
    "murah": r"\b(?:murah|termurah)\b",
    "original": r"\b(?:original|ori|asli)\b",
    "official": r"\bofficial\b",
    "promo": r"\bpromo\b",
    "import": r"\bimport\b",
    "mewah": r"\b(?:mewah|luxury)\b",
    "terlaris": r"\b(?:terlaris|best seller|bestseller)\b",
    "grosir": r"\bgrosir\b",
}


@st.cache_data
def muat_data():
    return pd.read_csv("Dataset/processed/produk_bersih.csv")


df = muat_data()

st.title("Pasar Produk")
st.caption("Listing produk Tokopedia: harga, wilayah, diskon, dan kata kunci di nama produk")

utama, panel = st.columns([3.3, 1], gap="large")

# ------------------------------------------------------------------ Panel kanan: filter
with panel:
    with st.container(key="kartu-filter"):
        st.subheader("Filter")
        pilihan_kategori = st.multiselect(
            "Kategori",
            options=sorted(df["kategori"].unique()),
            placeholder="Semua kategori",
        )
        pilihan_provinsi = st.multiselect(
            "Provinsi",
            options=sorted(df["provinsi"].dropna().unique()),
            placeholder="Semua provinsi",
        )
        # Harga sangat miring, jadi slider memakai titik-titik harga yang sudah ditentukan,
        # bukan skala rata dari 0 sampai Rp900 juta
        TITIK_HARGA = [0, 10_000, 25_000, 50_000, 100_000, 250_000, 500_000,
                       1_000_000, 5_000_000, 10_000_000, int(df["harga"].max())]
        harga_min, harga_maks = st.select_slider(
            "Rentang harga",
            options=TITIK_HARGA,
            value=(TITIK_HARGA[0], TITIK_HARGA[-1]),
            format_func=rupiah,
        )

        # Filter yang kosong berarti semua data dipakai
        data = df[df["harga"].between(harga_min, harga_maks)]
        if pilihan_kategori:
            data = data[data["kategori"].isin(pilihan_kategori)]
        if pilihan_provinsi:
            data = data[data["provinsi"].isin(pilihan_provinsi)]

        st.caption(f"{angka(len(data))} dari {angka(len(df))} produk sesuai filter")

    with st.container(key="kartu-tentang-data"):
        st.subheader("Tentang data")
        st.caption(
            "29.519 listing produk Tokopedia dari Kaggle, dibersihkan menjadi 29.068 produk. "
            "Jumlah terjual adalah batas bawah, karena \"1rb+\" berarti minimal 1.000. "
            "Kategori dibuat dari kata kunci nama produk. Dari 200 produk acak yang diperiksa manual, "
            "sekitar 90% produk yang diberi kategori tergolong dengan benar."
        )

# ------------------------------------------------------------------ Area utama
with utama:
    if data.empty:
        st.warning("Tidak ada produk yang sesuai filter. Coba longgarkan pilihan filter.")
        st.stop()

    kolom1, kolom2, kolom3, kolom4 = st.columns(4)
    with kolom1:
        kartu_kpi("Jumlah produk", angka(len(data)), "listing sesuai filter", sorot=True)
    with kolom2:
        kartu_kpi("Jumlah toko", angka(data["nama_toko"].nunique()), "nama toko berbeda")
    with kolom3:
        kartu_kpi("Median harga", rupiah(data["harga"].median()), "harga produk di tengah")
    with kolom4:
        kartu_kpi("Produk berdiskon", persen((data["diskon"] > 0).mean()), "diskon di atas 0%")

    st.write("")

    with st.container(key="kartu-analisis"):
        tab_harga, tab_wilayah, tab_diskon, tab_kata = st.tabs(
            ["Harga", "Wilayah", "Diskon & Rating", "Kata Kunci"]
        )

        # ---------------------------------------------------------- Tab Harga
        with tab_harga:
            st.subheader("Median harga per kategori")
            median_harga = data.groupby("kategori", as_index=False)["harga"].median()
            st.altair_chart(
                latar_putih(batang_horizontal(median_harga, "kategori", "harga", "Median harga (Rp)")),
                width="stretch",
            )

            st.subheader("Rentang harga per kategori")
            st.caption("Q1 dan Q3 adalah batas bawah dan atas dari 50% produk di tengah.")
            rentang = (
                data.groupby("kategori")["harga"]
                .agg(
                    jumlah_produk="size",
                    q1=lambda s: s.quantile(0.25),
                    median="median",
                    q3=lambda s: s.quantile(0.75),
                )
                .sort_values("median", ascending=False)
            )
            st.dataframe(
                rentang.style.format({"jumlah_produk": angka, "q1": rupiah, "median": rupiah, "q3": rupiah}),
                width="stretch",
            )

        # ---------------------------------------------------------- Tab Wilayah
        with tab_wilayah:
            data_wilayah = data.dropna(subset=["kota"])
            st.caption(
                f"{angka(len(data) - len(data_wilayah))} produk tanpa informasi lokasi "
                "(misalnya berlokasi \"Indonesia\") tidak diikutkan."
            )

            if data_wilayah.empty:
                st.info("Tidak ada produk dengan informasi lokasi untuk filter ini.")
            else:
                st.subheader("10 kota dengan jumlah toko terbanyak")
                toko_kota = (
                    data_wilayah.groupby("kota", as_index=False)["nama_toko"]
                    .nunique()
                    .rename(columns={"nama_toko": "jumlah_toko"})
                    .nlargest(10, "jumlah_toko")
                )
                st.altair_chart(
                    latar_putih(batang_horizontal(toko_kota, "kota", "jumlah_toko", "Jumlah toko")),
                    width="stretch",
                )

                st.subheader("Ringkasan per provinsi")
                provinsi = (
                    data.dropna(subset=["provinsi"])
                    .groupby("provinsi")
                    .agg(
                        jumlah_toko=("nama_toko", "nunique"),
                        jumlah_produk=("nama_produk", "size"),
                        total_terjual=("terjual", "sum"),
                        median_terjual=("terjual", "median"),
                    )
                    .sort_values("jumlah_toko", ascending=False)
                )
                provinsi["porsi_terjual"] = provinsi["total_terjual"] / provinsi["total_terjual"].sum()
                st.dataframe(
                    provinsi.style.format({
                        "jumlah_toko": angka,
                        "jumlah_produk": angka,
                        "total_terjual": angka,
                        "median_terjual": angka,
                        "porsi_terjual": lambda v: persen(v, 1),
                    }),
                    width="stretch",
                )
                st.caption(
                    "Total terjual sangat dipengaruhi segelintir produk yang sangat laris. "
                    "Jumlah toko dan median terjual lebih stabil untuk membandingkan wilayah."
                )

        # ---------------------------------------------------------- Tab Diskon & Rating
        with tab_diskon:
            kiri, kanan = st.columns(2, gap="large")

            with kiri:
                st.subheader("Produk laris per besar diskon")
                kelompok_diskon = pd.cut(
                    data["diskon"],
                    bins=[-0.1, 0, 10, 25, 50, 100],
                    labels=["0%", "1-10%", "11-25%", "26-50%", ">50%"],
                )
                per_diskon = (
                    data.groupby(kelompok_diskon, observed=True)
                    .agg(
                        jumlah_produk=("terjual", "size"),
                        persen_laris=("terjual", lambda s: (s >= 1_000).mean() * 100),
                    )
                    .reset_index()
                    .rename(columns={"diskon": "besar_diskon"})
                )
                grafik_diskon = (
                    alt.Chart(per_diskon)
                    .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                    .encode(
                        x=alt.X("besar_diskon:N", title="Besar diskon", sort=None, axis=alt.Axis(labelAngle=0)),
                        y=alt.Y("persen_laris:Q", title="Produk laris (%)"),
                        color=alt.condition(alt.datum.besar_diskon == "0%", alt.value(ABU), alt.value(HIJAU)),
                        tooltip=[
                            alt.Tooltip("besar_diskon:N", title="Diskon"),
                            alt.Tooltip("persen_laris:Q", title="Produk laris (%)", format=".1f"),
                            alt.Tooltip("jumlah_produk:Q", title="Jumlah produk", format=","),
                        ],
                    )
                )
                st.altair_chart(latar_putih(grafik_diskon), width="stretch")
                st.caption(
                    "Produk laris = terjual minimal 1.000. Produk berdiskon cenderung lebih laris, "
                    "tetapi diskon besar tidak menjamin produk laris, dan hubungan ini belum tentu sebab-akibat."
                )

            with kanan:
                st.subheader("Median terjual per rating")
                kelompok_rating = pd.cut(
                    data["rating"],
                    bins=[0, 4.5, 4.7, 4.8, 4.9, 5.0],
                    labels=["4.5 ke bawah", "4.6-4.7", "4.8", "4.9", "5.0"],
                )
                per_rating = (
                    data.groupby(kelompok_rating, observed=True)
                    .agg(
                        jumlah_produk=("terjual", "size"),
                        median_terjual=("terjual", "median"),
                        median_ulasan=("jumlah_ulasan", "median"),
                    )
                    .reset_index()
                )
                grafik_rating = (
                    alt.Chart(per_rating)
                    .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                    .encode(
                        x=alt.X("rating:N", title="Rating", sort=None, axis=alt.Axis(labelAngle=0)),
                        y=alt.Y("median_terjual:Q", title="Median terjual"),
                        color=alt.condition(alt.datum.rating == "5.0", alt.value(ORANYE), alt.value(HIJAU)),
                        tooltip=[
                            alt.Tooltip("rating:N", title="Rating"),
                            alt.Tooltip("median_terjual:Q", title="Median terjual", format=","),
                            alt.Tooltip("median_ulasan:Q", title="Median ulasan", format=","),
                            alt.Tooltip("jumlah_produk:Q", title="Jumlah produk", format=","),
                        ],
                    )
                )
                st.altair_chart(latar_putih(grafik_rating), width="stretch")
                st.caption(
                    "Rating 5.0 umumnya berasal dari produk yang baru punya sedikit pembeli, "
                    "sehingga median terjualnya justru rendah. Arahkan kursor ke batang untuk melihat median ulasan."
                )

        # ---------------------------------------------------------- Tab Kata Kunci
        with tab_kata:
            st.subheader("Harga produk dibanding median kategorinya")
            st.caption(
                "Indeks harga = harga produk dibagi median harga kategorinya. "
                "Indeks 1,0 berarti sama dengan median kategori, 2,0 berarti dua kali lipat."
            )

            nama = data["nama_produk"].str.lower()
            indeks_harga = data["harga"] / data.groupby("kategori")["harga"].transform("median")

            MIN_PRODUK = 20
            hasil = []
            for kata, pola in KATA_KUNCI.items():
                ada = nama.str.contains(pola, regex=True)
                if ada.sum() >= MIN_PRODUK:
                    hasil.append({
                        "kata_kunci": kata,
                        "jumlah_produk": int(ada.sum()),
                        "median_harga": data.loc[ada, "harga"].median(),
                        "indeks_harga": indeks_harga[ada].median(),
                    })

            if not hasil:
                st.info(f"Tidak ada kata kunci yang muncul di minimal {MIN_PRODUK} produk untuk filter ini.")
            else:
                kata_kunci = pd.DataFrame(hasil)
                kata_kunci["arah"] = kata_kunci["indeks_harga"].map(lambda v: "di atas" if v >= 1 else "di bawah")
                dasar = alt.Chart(kata_kunci).encode(
                    y=alt.Y("kata_kunci:N", title=None, sort="-x"),
                )
                batang = dasar.mark_bar(cornerRadius=4).encode(
                    x=alt.X("indeks_harga:Q", title="Indeks harga (1,0 = median kategori)"),
                    x2=alt.datum(1),
                    color=alt.Color(
                        "arah:N",
                        scale=alt.Scale(domain=["di atas", "di bawah"], range=[HIJAU, ORANYE]),
                        legend=alt.Legend(title="Dibanding median kategori", orient="bottom"),
                    ),
                    tooltip=[
                        alt.Tooltip("kata_kunci:N", title="Kata kunci"),
                        alt.Tooltip("indeks_harga:Q", title="Indeks harga", format=".2f"),
                        alt.Tooltip("median_harga:Q", title="Median harga (Rp)", format=",.0f"),
                        alt.Tooltip("jumlah_produk:Q", title="Jumlah produk", format=","),
                    ],
                )
                garis = alt.Chart(pd.DataFrame({"x": [1]})).mark_rule(color="#52514e").encode(x="x:Q")
                st.altair_chart(latar_putih(batang + garis), width="stretch")
                st.caption(
                    f"Hanya kata kunci yang muncul di minimal {MIN_PRODUK} produk yang ditampilkan. "
                    "\"Premium\" cenderung berada di bawah median kategorinya, jadi lebih berfungsi sebagai kata pemasaran."
                )
