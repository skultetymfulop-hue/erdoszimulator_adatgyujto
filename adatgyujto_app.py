import streamlit as st
import numpy as np
import pandas as pd
import math
import gspread
import datetime
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. KONSTANSOK ---
WIDTH, HEIGHT = 1500, 1500
L_TRANSSECT = math.sqrt(WIDTH**2 + HEIGHT**2)
R_BIG, R_SMALL = 564, 126
CENTER_BIG = (WIDTH/2, HEIGHT/2)
CENTERS_SMALL = [
    (WIDTH/4, HEIGHT/4), (3*WIDTH/4, HEIGHT/4), 
    (WIDTH/4, 3*HEIGHT/4), (3*WIDTH/4, 3*HEIGHT/4)
]
AREA_BIG = math.pi * (R_BIG**2)
AREA_SMALL_TOTAL = 4 * (math.pi * (R_SMALL**2))

# --- 2. FÜGGVÉNYEK ---

def save_to_sheets(row):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Hitelesítési adatok a megadott JSON alapján
        creds_dict = {
            "type": "service_account",
            "project_id": "genial-acronym-489918-a6",
            "private_key_id": "85c43711722d4586bfaca301bf5e186b41d923f1",
            "private_key": st.secrets["gspread"]["private_key"] if "gspread" in st.secrets else """-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDpIW15OnV0ZZKV\nlE5jPM5QQL0malqFnK3RjQ4V0N/wTZFw3sJ4oXybXY266xZ3bEbiCjiAy57Kuzhk\nbU5gHuLM3+PBsO99wCDLJSe1QwV90E0hqWeHuTksaSy68FwoBbiAk9jB7SR3Ormq\nbXQnzCLpwaU5Fs2x/Paq7WSEGU7PR+wklXukO5yCXhcIwh/4//fkWbVmYght7k2h\nCnXPOoyXNEPGvbDtc01u26C6jZCw9b3iKZpGadkYUfyQxEEX6TXn0ExrqYg5AOpG\nb9YeNdeQMtkEC6rMP1kbRwYEBoJLmATHfbIrm2ig1dMPJPuvA9EhEuknzIFtuM1h\nfYX+cDxNAgMBAAECggEAEDzmj+DRQQX5H4eIrTNVSHQ16IjUXMWUusmJH15g1q9E\nb9joMThIQlcSEeChfDhzuHdPR7NHEGZZb29Im/vSvsPibIGLMNZSwmuIWED+jyyU\nzsEqp6KwV4ZM2gl3VcdOOlBx8tH2bgKOX49HnaUDkoYNIMyUj67nrHCkBWpw2ZGO\nGXZjpZ4gWPOgWwS9B9vJpo7YoQo94TJ54wV346aF/QAKZvgOB9xjWK/oFiipTUIN\niSUvjuq5td50A/oofvYki7sdX4uN1CiCN9rlSpz41LJ9xr2RAWkuWhwDGnH0cP8Y\nFn2+oWPtH66AdHs8cUl4PVdbehUZ3cLZth+0vD6JqQKBgQD3fTZJDAB48dPMeyIO\nl4GacMQ2svAh1u3ECEpx+WUZxCArS6nRus3+58b2i3A/Sd6rS4rrP6eMXsYz5/DA\nSqtIsOISfrvy5oT1k/NloMGAoTnLKKbnOpoE+sCTV0z14LS91K7kt+ZUaZaHlJyx\nab1J+d/5LHFf2Vw2KD5rdXYFWQKBgQDxJc8ouU3Uhtp/y34NK1QihJ54uHi0hrC6\naohb0jitf7mgfjFNBmbR4Z/0+spKd5KFQDL+tovAvS6jYgbq8a/4BHY7ruCiq/xu\ntgp5A5ZwxxvMYeML8aXKYzbXfAAXiA/71gFPwDMtq8OyVXcs5Xp8ghacu0rCFGmh\nnT7GajqsFQKBgHijdnTA/vH1n3KLixxlye1IjrzDGL7GD/yAthk8ooWezreMGGl9\nj7Bzts6zRbH0BjClkEAANWH9SMxAgWCahUfXwTuWv3M13xX+WqTtaaWT8aIQXNtV\n+4H14S1xXrh0ImZuaBphcksvdQr97CunCXgn7398pH8+au6TS2oCRddxAoGAbLha\nJIce4uGFozYwd2mAfiuCcvTgXquXBATBw3wM15QNMaGTQqHPO3LYtg9Xoqk0IuVl\n2FaevV/NphWs/sHGTzBbyd63IkAeCCAEqriGXAQ4sTW0so7Y6109vXsHY5SReD3s\ny3Lg4AdfrIhBubkgNwBDh5gdRVEEqruFMNl16F0CgYEAsMCuMflQvpCI9dBWEs2T\n/ZDkjDX9RQua6WptYJkNB6KgJGJliA+G7P6jVVf5l/E1ej4Qz1vlhbY1rFBWCNKo\njYVz1mcYvehrgVY1B2EJqP+Mp3UtLBp9rn7rhljLow8pZwc472PrufUtygcTs9hn\nzRNV/oST+dvRz7wXRgM5zt8=\n-----END PRIVATE KEY-----\n""",
            "client_email": "erdo-mentes@genial-acronym-489918-a6.iam.gserviceaccount.com",
            "client_id": "111987957484558081367",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/erdo-mentes%40genial-acronym-489918-a6.iam.gserviceaccount.com"
        }
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/10DyyNfaYh0C9orj-F_Go8Har46Tsm1JNISzecQ1dcIc/edit#gid=0").get_worksheet(0)
        
        # Ha teljesen üres a lap, tegyünk rá fejlécet
        if not sheet.get_all_values():
            sheet.append_row(["Timestamp", "In_density", "MAPE_density_T", "MAPE_density_M"])
            
        sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Sheet hiba: {e}")
        return False

def point_line_distance(px, py):
    # Átlós transzekt vonalának távolsága
    num = abs((WIDTH - 0) * (0 - py) - (0 - px) * (HEIGHT - 0))
    return num / L_TRANSSECT

def run_forest_simulation(params):
    target_intensity = params['intensity']
    expected_n = int(target_intensity * WIDTH * HEIGHT)
    n_final = np.random.poisson(expected_n)
    
    if n_final == 0:
        return pd.DataFrame(columns=["height", "T", "C"])
        
    x_coords = np.random.uniform(0, WIDTH, n_final)
    y_coords = np.random.uniform(0, HEIGHT, n_final)
    
    shape_k = params['shape_k']
    mode = params['mode']
    theta = mode / (shape_k - 1) if shape_k > 1 else mode
    heights = np.clip(np.random.gamma(shape=shape_k, scale=theta, size=n_final), 3, 300)
    
    results = []
    for i in range(n_final):
        h = float(heights[i])
        px, py = float(x_coords[i]), float(y_coords[i])
        
        # Transzekt (T)
        dist_t = point_line_distance(px, py)
        in_t = 1 if dist_t <= h else 0
        
        # Mintakör (C)
        in_c = 0
        dist_to_center = math.sqrt((px - CENTER_BIG[0])**2 + (py - CENTER_BIG[1])**2)
        if h >= 50 and dist_to_center <= R_BIG:
            in_c = 1
        elif h < 50:
            for sx, sy in CENTERS_SMALL:
                if math.sqrt((px - sx)**2 + (py - sy)**2) <= R_SMALL:
                    in_c = 1
                    break
        
        results.append({"height": h, "T": in_t, "C": in_c})
        
    return pd.DataFrame(results)

# --- 3. UI ---
st.title("🌲 MAPE Adatrögzítő Szimulátor")
st.markdown("Minden gombnyomás **100 futást** végez el és az átlagolt hibát menti a Google Sheets-be.")

in_intensity = st.sidebar.slider("Cél sűrűség (db/cm²)", 0.0005, 0.0050, 0.0020, format="%.4f")
in_mode = st.sidebar.slider("Módusz (magasság)", 5, 50, 15)
in_shape = st.sidebar.slider("Változatosság (shape)", 1.2, 5.0, 2.0)

if st.button("ANALÍZIS INDÍTÁSA ÉS MENTÉS", use_container_width=True):
    all_runs_errors = []
    progress_bar = st.progress(0)
    
    for run in range(100):
        sim_params = {'intensity': in_intensity, 'mode': in_mode, 'shape_k': in_shape}
        df = run_forest_simulation(sim_params)
        
        # 1. Valódi érték
        true_density = len(df) / (WIDTH * HEIGHT)
        
        # 2. Transzekt becslés
        t_df = df[df['T'] == 1]
        t_density = (1 / (2.0 * t_df['height'] * L_TRANSSECT)).sum() if not t_df.empty else 0
        
        # 3. Mintakör becslés
        c_df = df[df['C'] == 1]
        d_small = (len(c_df[c_df['height'] < 50]) / AREA_SMALL_TOTAL)
        d_big = (len(c_df[c_df['height'] >= 50]) / AREA_BIG)
        c_density = d_small + d_big
        
        # Hiba számítás
        if true_density > 0:
            all_runs_errors.append({
                't_err': abs(true_density - t_density) / true_density,
                'c_err': abs(true_density - c_density) / true_density
            })
        
        progress_bar.progress((run + 1) / 100)
    
    # MAPE számítása
    err_df = pd.DataFrame(all_runs_errors)
    mape_t = err_df['t_err'].mean() * 100
    mape_c = err_df['c_err'].mean() * 100
    
    # Sor rögzítése
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row_to_save = [timestamp, in_intensity, f"{mape_t:.2f}%", f"{mape_c:.2f}%"]
    
    if save_to_sheets(row_to_save):
        st.success("✅ Sikeres mentés a Google Sheets-be!")
        st.write("Rögzített adatok:", pd.DataFrame([row_to_save], columns=["Idő", "Sűrűség", "T-MAPE", "M-MAPE"]))
    else:
        st.error("❌ A mentés sikertelen volt.")
