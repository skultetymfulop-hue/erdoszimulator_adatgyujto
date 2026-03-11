import streamlit as st
import numpy as np
import pandas as pd
import math
import gspread
import datetime
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. ALAPBEÁLLÍTÁSOK ---
WIDTH, HEIGHT = 1500, 1500
R_CORE = 5
L_TRANSSECT = math.sqrt(WIDTH**2 + HEIGHT**2)
R_BIG, R_SMALL = 564, 126
CENTER_BIG = (WIDTH/2, HEIGHT/2)
CENTERS_SMALL = [(WIDTH/4, HEIGHT/4), (3*WIDTH/4, HEIGHT/4), (WIDTH/4, 3*HEIGHT/4), (3*WIDTH/4, 3*HEIGHT/4)]
AREA_BIG = math.pi * (R_BIG**2)
AREA_SMALL_TOTAL = 4 * (math.pi * (R_SMALL**2))

# --- 2. FÜGGVÉNYEK ---

def save_to_sheets(row):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # A te adataid a JSON-ból
        creds_dict = {
            "type": "service_account",
            "project_id": "genial-acronym-489918-a6",
            "private_key_id": "85c43711722d4586bfaca301bf5e186b41d923f1",
            "private_key": st.secrets["gspread"]["private_key"] if "gspread" in st.secrets else "-----BEGIN PRIVATE KEY-----\n...", # Itt a teljes kulcsod kell ha nincs secrets
            "client_email": "erdo-mentes@genial-acronym-489918-a6.iam.gserviceaccount.com",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        # Megjegyzés: A private_key-t a legegyszerűbb a Streamlit Secrets-be tenni!
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/10DyyNfaYh0C9orj-F_Go8Har46Tsm1JNISzecQ1dcIc/edit#gid=0").get_worksheet(0)
        sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Sheet hiba: {e}")
        return False

def point_line_distance(x, y):
    # Átlós transzekt (0,0-tól WIDTH, HEIGHT-ig)
    return abs((WIDTH - 0) * (0 - y) - (0 - x) * (HEIGHT - 0)) / L_TRANSSECT

def run_forest_simulation(params):
    expected_n = int(params['intensity'] * WIDTH * HEIGHT)
    n_target = np.random.poisson(expected_n)
    
    # Pontok generálása (egyszerűsített gyors verzió a 100 futáshoz)
    x = np.random.uniform(0, WIDTH, n_target)
    y = np.random.uniform(0, HEIGHT, WIDTH) # Javítva n_target-re
    x = np.random.uniform(0, WIDTH, n_target)
    y = np.random.uniform(0, HEIGHT, n_target)
    
    shape_k, mode = params['shape_k'], params['mode']
    theta = mode / (shape_k - 1) if shape_k > 1 else mode
    heights = np.clip(np.random.gamma(shape=shape_k, scale=theta, size=n_target), 3, 300)
    
    results = []
    for i in range(n_target):
        h = float(heights[i])
        px, py = float(x[i]), float(y[i])
        
        # Transzekt (T)
        in_t = 1 if point_line_distance(px, py) <= h else 0
        
        # Mintakör (C)
        in_c = 0
        dist_c = math.sqrt((px - CENTER_BIG[0])**2 + (py - CENTER_BIG[1])**2)
        if (h >= 50 and dist_c <= R_BIG):
            in_c = 1
        elif h < 50:
            for sx, sy in CENTERS_SMALL:
                if math.sqrt((px - sx)**2 + (py - sy)**2) <= R_SMALL:
                    in_c = 1
                    break
        
        results.append({"height": h, "T": in_t, "C": in_c})
    return pd.DataFrame(results)

# --- 3. UI ---
st.title("🌲 MAPE Adatrögzítő")

in_intensity = st.slider("Cél sűrűség (db/cm²)", 0.0005, 0.0050, 0.0020, format="%.4f")

if st.button("100 FUTÁS ÉS MENTÉS"):
    all_runs = []
    bar = st.progress(0)
    
    for r in range(100):
        df = run_forest_simulation({'intensity': in_intensity, 'mode': 15, 'shape_k': 2.0})
        
        # Valódi sűrűség
        true_dens = len(df) / (WIDTH * HEIGHT)
        
        # Transzekt becslés
        t_df = df[df['T'] == 1]
        t_dens = (1 / (2.0 * t_df['height'] * L_TRANSSECT)).sum() if not t_df.empty else 0
        
        # Mintakör becslés
        c_df = df[df['C'] == 1]
        d_small = (len(c_df[c_df['height'] < 50]) / AREA_SMALL_TOTAL)
        d_big = (len(c_df[c_df['height'] >= 50]) / AREA_BIG)
        c_dens = d_small + d_big
        
        all_runs.append({
            't_err': abs(true_dens - t_dens) / true_dens if true_dens > 0 else 0,
            'c_err': abs(true_dens - c_dens) / true_dens if true_dens > 0 else 0
        })
        bar.progress(r + 1)

    errors = pd.DataFrame(all_runs)
    mape_t = errors['t_err'].mean() * 100
    mape_c = errors['c_err'].mean() * 100
    
    # Mentés
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    row = [now, in_intensity, f"{mape_t:.2f}%", f"{mape_c:.2f}%"]
    
    if save_to_sheets(row):
        st.success(f"Mentve! T-MAPE: {mape_t:.2f}%, M-MAPE: {mape_c:.2f}%")
        st.write("Google Sheets sor:", row)
