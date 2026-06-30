import streamlit as st

# ----------------------------------------------------
# Trail & Bish Dynasty v1.0
# Application Entry
# CSS injection and chrome-hiding are handled by
# render_sidebar() on each page, so app.py only needs
# to configure the page and redirect.
# ----------------------------------------------------

st.set_page_config(
    page_title="Trail & Bish Boys Dynasty",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.switch_page("pages/Dashboard.py")
