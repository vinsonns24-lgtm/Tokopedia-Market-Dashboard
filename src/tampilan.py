"""Warna dan format angka yang dipakai di semua halaman dashboard."""

BIRU = "#2a78d6"
ORANYE = "#eb6834"
ABU = "#c8c6bf"
TEKS = "#52514e"


def rupiah(x):
    return "Rp" + f"{x:,.0f}".replace(",", ".")


def angka(x):
    return f"{x:,.0f}".replace(",", ".")
