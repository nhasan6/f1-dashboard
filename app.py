import streamlit as st

st.set_page_config(page_title="Formula 1 Live Dashboard", layout="wide") # TODO add a favicon
st.title("Formula 1 Dashboard")
# substitle - "The stopwatch never lies" - Toto Wolff
year = st.selectbox("Year", [2026, 2025, 2024, 2023]) # first option is selected by default (needs to be most recent year)
st.subheader(f"{year} Season Overview")

row1 = st.columns(3)
row2 = st.columns(3)

for col in row1 + row2:
    tile = col.container(height=120)
    tile.metric("metric", 20)

st.subheader("Championship Standings")

    