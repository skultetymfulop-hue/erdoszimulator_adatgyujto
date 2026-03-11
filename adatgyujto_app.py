import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.title("🧪 Google Sheets Kapcsolat Teszt")

# Kapcsolat teszt
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    st.success("✅ Kapcsolat létrehozva!")
    
    # Lista spreadsheet-ek (opcionális)
    sheets = conn.list_sheets()
    st.write("📋 Elérhető sheet-ek:", sheets)
    
except Exception as e:
    st.error(f"❌ Kapcsolat hiba: {e}")
    st.stop()

# Olvasás
try:
    df = conn.read()
    st.success("✅ Olvasás OK!")
    st.dataframe(df)
except Exception as e:
    st.error(f"❌ Olvasás hiba: {e}")

# Írás gomb
if st.button("✏️ Teszt írás"):
    data = pd.DataFrame({
        "Teszt": [f"OK - {pd.Timestamp.now()}"],
        "Felhasználó": ["Streamlit"]
    })
    conn.update(data=data)
    st.success("✅ Írás sikeres! Nézd meg a Sheet-et!")
    st.rerun()
