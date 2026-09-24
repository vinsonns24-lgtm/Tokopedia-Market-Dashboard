"""Warna, format angka, dan gaya tampilan yang dipakai di semua halaman dashboard."""

import streamlit as st

HIJAU = "#1baf7a"        # warna utama grafik
HIJAU_TUA = "#128c5e"    # kartu yang disorot dan elemen interaktif
ORANYE = "#eb6834"       # penanda hal yang perlu diperhatikan, misalnya ulasan negatif
ABU = "#c8c6bf"          # data pembanding
TEKS = "#52514e"

CSS = """
<style>
.block-container {
    padding-top: 2.2rem;
    padding-bottom: 3rem;
    max-width: 1400px;
}

/* Kartu putih: semua container yang key-nya diawali "kartu" */
[class*="st-key-kartu"] {
    background: #ffffff;
    border-radius: 18px;
    padding: 1.1rem 1.25rem 1.25rem 1.25rem;
    box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04), 0 8px 24px rgba(16, 24, 40, 0.05);
}

/* Kartu angka ringkasan */
.kpi {
    background: #ffffff;
    border-radius: 18px;
    padding: 1.1rem 1.25rem;
    box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04), 0 8px 24px rgba(16, 24, 40, 0.05);
    min-height: 118px;
}
.kpi-label {
    font-size: 0.8rem;
    font-weight: 500;
    color: #6b7280;
}
.kpi-nilai {
    font-size: 1.75rem;
    font-weight: 700;
    color: #111827;
    margin-top: 0.35rem;
    line-height: 1.2;
}
.kpi-catatan {
    font-size: 0.75rem;
    color: #8a94a3;
    margin-top: 0.25rem;
}
.kpi-sorot {
    background: #128c5e;
    box-shadow: 0 10px 24px rgba(18, 140, 94, 0.28);
}
.kpi-sorot .kpi-label,
.kpi-sorot .kpi-catatan {
    color: rgba(255, 255, 255, 0.92);
}
.kpi-sorot .kpi-nilai {
    color: #ffffff;
}

/* Judul halaman dan judul kartu */
h1 {
    font-size: 1.6rem !important;
}
[class*="st-key-kartu"] h3 {
    font-size: 1.02rem !important;
    padding-top: 0.2rem;
}
</style>
"""


def terapkan_gaya():
    st.markdown(CSS, unsafe_allow_html=True)


def kartu_kpi(label, nilai, catatan="", sorot=False):
    """Kartu angka ringkasan. Kartu dengan sorot=True berwarna hijau, seperti kartu utama."""
    kelas = "kpi kpi-sorot" if sorot else "kpi"
    st.markdown(
        f'<div class="{kelas}"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-nilai">{nilai}</div><div class="kpi-catatan">{catatan}</div></div>',
        unsafe_allow_html=True,
    )


# Format angka gaya Indonesia untuk grafik: koma untuk desimal, titik untuk ribuan
LOCALE_ANGKA = {"decimal": ",", "thousands": ".", "grouping": [3], "currency": ["Rp", ""]}


def latar_putih(grafik):
    """Latar grafik Altair dibuat putih supaya menyatu dengan kartu, dan angkanya memakai format Indonesia."""
    return grafik.configure(background="#ffffff", locale={"number": LOCALE_ANGKA})


def batang_horizontal(data, kolom_label, kolom_nilai, judul_nilai, format_nilai=",.0f"):
    """Grafik batang horizontal satu warna, diurutkan dari nilai terbesar."""
    import altair as alt

    return (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4, color=HIJAU)
        .encode(
            y=alt.Y(f"{kolom_label}:N", title=None, sort="-x"),
            x=alt.X(f"{kolom_nilai}:Q", title=judul_nilai),
            tooltip=[
                alt.Tooltip(f"{kolom_label}:N", title=kolom_label.replace("_", " ").capitalize()),
                alt.Tooltip(f"{kolom_nilai}:Q", title=judul_nilai, format=format_nilai),
            ],
        )
    )


def rupiah(x):
    return "Rp" + f"{x:,.0f}".replace(",", ".")


def angka(x):
    return f"{x:,.0f}".replace(",", ".")


def desimal(x, digit=2):
    """Bilangan desimal gaya Indonesia, misalnya 0.567 menjadi '0,57'."""
    return f"{x:.{digit}f}".replace(".", ",")


def persen(x, digit=0):
    """Proporsi (0 sampai 1) sebagai persen gaya Indonesia, misalnya 0.981 menjadi '98,1%'."""
    return desimal(x * 100, digit) + "%"
