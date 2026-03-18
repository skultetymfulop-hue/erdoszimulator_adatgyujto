import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.title("🧪 Google Sheets Kapcsolat Teszt")

# Kapcsolat
@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

conn = get_connection()

if "tesztelt" not in st.session_state:
    st.session_state.tesztelt = False

# 1. Olvasás teszt
try:
    st.header("📖 Olvasás teszt")
    df = conn.read(worksheet="Sheet1")  # Vagy "Example 1" ha van
    st.success("✅ Olvasás OK!")
    st.dataframe(df, use_container_width=True)
except Exception as e:
    st.error(f"❌ Olvasás hiba: {e}")

# 2. Írás teszt (gomb)
st.header("✏️ Írás teszt")
col1, col2 = st.columns(2)
with col1:
    datum = st.date_input("Dátum")
with col2:
    ertek = st.number_input("Érték", value=42.0)

if st.button("Írj új sort!"):
    uj_sor = pd.DataFrame({
        "Dátum": [datum],
        "Érték": [ertek],
        "Teszt": ["Streamlit teszt - " + pd.Timestamp.now().strftime("%H:%M")]
    })
    try:
        conn.update(worksheet="Sheet1", data=uj_sor)
        st.success("✅ Írás OK! Frissítsd az oldalt, és nézd meg a Sheet-et.")
        st.session_state.tesztelt = True
        st.rerun()
    except Exception as e:
        st.error(f"❌ Írás hiba: {e}")

# 3. Újraolvasás
if st.button("🔄 Újra olvass be"):
    st.rerun()
