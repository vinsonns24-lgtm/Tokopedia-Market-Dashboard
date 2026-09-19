import streamlit as st

from src.tampilan import terapkan_gaya

st.set_page_config(page_title="Product Intelligence Dashboard", layout="wide")
terapkan_gaya()

halaman = st.navigation(
    [
        st.Page("halaman/produk.py", title="Pasar Produk", icon=":material/storefront:", default=True),
        st.Page("halaman/ulasan.py", title="Analisis Ulasan", icon=":material/reviews:"),
    ],
    position="top",
)

halaman.run()
