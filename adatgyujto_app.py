import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("✅ Google Sheets Kapcsolat")

# Kapcsolat létrehozása
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Itt kényszerítjük, hogy használja a secrets-ben lévő URL-t
    url = st.secrets["gsheets"]["spreadsheet"]
    
    # Beolvasás az URL megadásával
    df = conn.read(spreadsheet=url, ttl=0)
    
    st.success("Sikerült az adatok beolvasása!")
    st.dataframe(df)

except Exception as e:
    st.error(f"Hiba: {e}")
    # Hibakereséshez: nézzük meg, mi van a gsheets alatt
    st.write("Titkok ellenőrzése (kulcsok):", list(st.secrets["gsheets"].keys()))
