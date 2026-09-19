"""Gaya grafik matplotlib untuk notebook, memakai palet yang sama dengan dashboard."""

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

BIRU, ORANYE, HIJAU = "#2a78d6", "#eb6834", "#1baf7a"
SERIES = [BIRU, ORANYE, HIJAU]
SEQ_BLUE = ["#cde2fb", "#86b6ef", "#3987e5", "#256abf", "#0d366b"]
# Konteks sekuensial kedua memakai rona slot berikutnya (oranye), supaya
# heatmap "pujian" dan "keluhan" tidak tertukar saat dibaca berdampingan.
SEQ_ORANGE = ["#fce0d3", "#f5a582", "#eb6834", "#c24e1f", "#8a3310"]

CMAP_BIRU = LinearSegmentedColormap.from_list("biru", SEQ_BLUE)
CMAP_ORANYE = LinearSegmentedColormap.from_list("oranye", SEQ_ORANGE)


def terapkan() -> None:
    plt.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "axes.edgecolor": AXIS,
        "axes.labelcolor": INK_2,
        "axes.titlecolor": INK,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.grid": True,
        "axes.axisbelow": True,
        "axes.grid.axis": "x",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.prop_cycle": plt.cycler(color=SERIES),
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelcolor": INK_2,
        "ytick.labelcolor": INK_2,
        "font.family": "sans-serif",
        "font.size": 11,
        "figure.dpi": 110,
        "figure.figsize": (9, 4.5),
    })


def rupiah(nilai: float) -> str:
    if nilai >= 1e12:
        return f"Rp{nilai / 1e12:.1f} T"
    if nilai >= 1e9:
        return f"Rp{nilai / 1e9:.1f} M"
    if nilai >= 1e6:
        return f"Rp{nilai / 1e6:.1f} jt"
    if nilai >= 1e3:
        return f"Rp{nilai / 1e3:.0f} rb"
    return f"Rp{nilai:,.0f}"
