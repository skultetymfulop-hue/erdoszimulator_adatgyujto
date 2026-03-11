import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("🚀 Google Sheets Kapcsolat Teszt")

# Kapcsolat létrehozása a secrets.toml alapján
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Adatok beolvasása (az első munkalapról)
    # A ttl=0 biztosítja, hogy ne gyorsítótárazott adatot láss
    df = conn.read(spreadsheet=st.secrets["connections.gsheets"]["spreadsheet"], ttl=0)

    st.success("Siker! A kapcsolat él.")
    
    st.write("Itt vannak a táblázatod adatai:")
    st.dataframe(df)

except Exception as e:
    st.error("Hiba történt a kapcsolódás során:")
    st.code(e)
