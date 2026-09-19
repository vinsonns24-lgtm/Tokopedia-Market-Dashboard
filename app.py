import streamlit as st

st.set_page_config(page_title="Product Intelligence Dashboard", layout="wide")

halaman = st.navigation([
    st.Page("halaman/produk.py", title="Pasar Produk", icon=":material/storefront:", default=True),
    st.Page("halaman/ulasan.py", title="Suara Pembeli", icon=":material/reviews:"),
])

st.sidebar.caption("Product Intelligence Dashboard: riset pasar Tokopedia dari sisi penjual dan pembeli.")

halaman.run()
