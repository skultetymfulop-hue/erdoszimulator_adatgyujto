import streamlit as st

st.title("🔐 Secrets Ellenőrző")

# 1. Alapszintű ellenőrzés: Létezik-e bármilyen secret?
if not st.secrets:
    st.error("❌ A Streamlit egyáltalán nem lát semmilyen titkosított adatot (secrets).")
    st.info("Ha Cloud-on vagy: Ellenőrizd a 'Settings > Secrets' fület. Ha saját gépen: '.streamlit/secrets.toml' fájlt.")
else:
    st.success("✅ A Streamlit látja a secrets tárolót.")

    # 2. Kulcs-hierarchia ellenőrzése
    all_keys = list(st.secrets.keys())
    st.write(f"Elérhető fő kulcsok: `{all_keys}`")

    # Megnézzük a konkrét elérési utat
    try:
        if "connections.gsheets" in st.secrets:
            gsheets = st.secrets["connections.gsheets"]
            st.success("🎯 'connections.gsheets' szekció megtalálva!")
            
            # Csak a nem titkos adatokat íratjuk ki tesztnek
            st.info(f"Project ID a fájlban: {gsheets.get('project_id', 'Nincs megadva')}")
            st.info(f"Email a fájlban: {gsheets.get('client_email', 'Nincs megadva')}")
            
            if "private_key" in gsheets:
                st.success("🔑 A Private Key kulcs jelen van.")
            else:
                st.warning("⚠️ A 'private_key' kulcs hiányzik a szekcióból!")
        else:
            st.error("❌ A 'connections.gsheets' kulcs nem található.")
            st.write("Próbáld meg ezt a struktúrát a Secrets-ben:")
            st.code("[connections.gsheets]\nspreadsheet = '...' \n...")
    except Exception as e:
        st.exception(e)

# 3. Tipp a javításhoz
st.divider()
st.write("### Gyorssegély:")
st.markdown("""
1. **Pontos név:** A fájl neve `.streamlit/secrets.toml` legyen (Windows-on is!).
2. **Nincs behúzás:** A `[connections.gsheets]` sor előtt ne legyen szóköz.
3. **Idézőjelek:** Minden érték (spreadsheet URL, email, stb.) legyen idézőjelben.
""")
