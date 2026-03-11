import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.title("🧪 Google Sheets Kapcsolat TESZT")

# Kapcsolat létrehozása
@st.cache_resource
def get_connection():
    return st.connection("gsheets", type=GSheetsConnection)

conn = get_connection()
st.success("✅ Kapcsolat OK!")

# 1. Olvasás teszt (ELSŐ worksheet automatikusan)
st.header("📖 Olvasás teszt")
try:
    df = conn.read()  # Nincs worksheet paraméter!
    st.success("✅ Olvasás SIKERES!")
    st.dataframe(df, use_container_width=True)
except Exception as e:
    st.error(f"❌ Olvasás hiba: {e}")

# 2. Írás teszt
st.header("✏️ Írás teszt")
col1, col2 = st.columns(2)
with col1:
    nev = st.text_input("Név", "Tesztelő")
with col2:
    ertek = st.number_input("Érték", value=100)

if st.button("🟢 ÍRJ ÚJ SORT!", type="primary"):
    try:
        # Új sor hozzáadása
        new_data = pd.DataFrame({
            "Név": [nev],
            "Érték": [ertek],
            "Időpont": [pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")]
        })
        conn.update(data=new_data)  # Nincs worksheet!
        st.success("✅ ÍRÁS SIKERES! Frissítsd az oldalt!")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Írás hiba: {e}")

st.info("💡 Ellenőrizd a Google Sheet-et új sorokért!")
