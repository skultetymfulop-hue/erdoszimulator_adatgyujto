import streamlit as st
import numpy as np
import pandas as pd
import math
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. GOOGLE SHEETS KAPCSOLAT BEÁLLÍTÁSA ---
def save_to_google_sheets(data_row):
    # Hitelesítési adatok a megadott JSON alapján
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Itt a megadott adataidat használjuk
    creds_dict = {
        "type": "service_account",
        "project_id": "genial-acronym-489918-a6",
        "private_key_id": "85c43711722d4586bfaca301bf5e186b41d923f1",
        "private_key": st.secrets["gspread"]["private_key"] if "gspread" in st.secrets else "A_TE_PRIVATE_KEY_STRINGED",
        "client_email": "erdo-mentes@genial-acronym-489918-a6.iam.gserviceaccount.com",
        "client_id": "111987957484558081367",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/erdo-mentes%40genial-acronym-489918-a6.iam.gserviceaccount.com"
    }
    
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        # Megnyitás URL alapján
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/10DyyNfaYh0C9orj-F_Go8Har46Tsm1JNISzecQ1dcIc/edit#gid=0").get_worksheet(0)
        
        # Ha a táblázat üres, fejléc hozzáadása
        if not sheet.get_all_values():
            sheet.append_row(["ID", "In_density", "MAPE_density_T", "MAPE_density_M", "Timestamp"])
            
        sheet.append_row(data_row)
        return True
    except Exception as e:
        st.error(f"Hiba a mentés során: {e}")
        return False

# --- 2. ALAPBEÁLLÍTÁSOK ÉS SZIMULÁCIÓS MOTOR ---
# (A korábbi run_forest_simulation és get_weighted_height_mean függvények változatlanok maradnak)

# --- 3. UI ÉS LOGIKA ---
st.title("🌲 MAPE Adatrögzítő & Szimulátor")

if 'local_history' not in st.session_state:
    st.session_state['local_history'] = []

with st.sidebar:
    st.header("⚙️ Paraméterek")
    in_intensity = st.slider("Cél sűrűség", 0.0005, 0.005, 0.0020, format="%.4f")
    # ... többi csúszka (mode, shape, grav_str, chewed_p) ...

if st.button("100 FUTÁS ÉS MENTÉS A FELHŐBE", use_container_width=True):
    all_errors = []
    progress = st.progress(0)
    
    for i in range(100):
        # Szimuláció futtatása (paraméterekkel)
        df = run_forest_simulation({
            'intensity': in_intensity, 'mode': 15, 'shape_k': 2.0, 
            'grav_str': 3, 'chewed_p': 30, 'n_grav': 3
        })
        
        # Sűrűség számítások
        s_dens = len(df) / (1500 * 1500)
        # T és C becslések (korábbi logika alapján)
        # ... (t_density és c_density kiszámítása) ...
        
        all_errors.append({
            't_err': abs(s_dens - t_density)/s_dens if s_dens > 0 else 0,
            'c_err': abs(s_dens - c_density)/s_dens if s_dens > 0 else 0
        })
        progress.progress((i + 1) / 100)

    # MAPE számítás
    err_df = pd.DataFrame(all_errors)
    mape_t = err_df['t_err'].mean() * 100
    mape_c = err_df['c_err'].mean() * 100
    
    # Sor összeállítása mentéshez
    import datetime
    new_id = len(st.session_state['local_history']) + 1
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [new_id, in_intensity, f"{mape_t:.2f}%", f"{mape_c:.2f}%", timestamp]
    
    # Mentés a Google Sheets-be
    if save_to_google_sheets(row):
        st.success("✅ Adatok sikeresen rögzítve a Google Táblázatban!")
        st.session_state['local_history'].append(row)

# --- TÁBLÁZAT MEGJELENÍTÉSE ---
if st.session_state['local_history']:
    st.subheader("📊 Aktuális munkamenet eredményei")
    history_df = pd.DataFrame(
        st.session_state['local_history'], 
        columns=["ID", "In_density", "MAPE_density_T", "MAPE_density_M", "Időpont"]
    )
    st.table(history_df)
