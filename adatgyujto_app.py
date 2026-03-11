import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("✅ Google Sheets Kapcsolat Sikerült!")

# Mivel a secrets-ben [gsheets] van, itt is ezt a nevet adjuk meg
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Adatok beolvasása
    df = conn.read(ttl=0)
    
    st.success("Az adatok beolvasása sikeres!")
    st.dataframe(df)

except Exception as e:
    st.error(f"Valami mégsem kerek: {e}")
    st.write("Próbáljuk meg direktben:")
    # Ha a fenti nem menne, ez a biztos:
    try:
        conn_direct = st.connection("gsheets", type=GSheetsConnection, **st.secrets["gsheets"])
        df_direct = conn_direct.read(ttl=0)
        st.dataframe(df_direct)
    except:
        st.write("Még a direkt hívás is hibát dob.")
