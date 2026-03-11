import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("🚀 Google Sheets Végső Teszt")

# Megpróbáljuk a lehető legegyszerűbben
try:
    # A kapcsolat létrehozása
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Direkt megadjuk a linket a biztonság kedvéért, levágva a felesleget
    sheet_url = st.secrets["gsheets"]["spreadsheet"].split("#")[0]
    
    # Adatok beolvasása
    df = conn.read(spreadsheet=sheet_url, ttl=0)
    
    st.success("Siker! Az adatok megérkeztek:")
    st.dataframe(df)

except Exception as e:
    st.error(f"Hiba történt: {e}")
    st.info("Ha 404-et látsz, ellenőrizd, hogy a Google Táblázatban a 'Megosztás' gombnál hozzáadtad-e a service account email címét!")
