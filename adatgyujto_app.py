import streamlit as st
import numpy as np
import pandas as pd
import math
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.patches as patches
import plotly.express as px
from streamlit_gsheets import GSheetsConnection  # ← EZT add hozzá!

# --- 1. ALAPBEÁLLÍTÁSOK ---
st.set_page_config(page_title="Profi Erdő Szimulátor", layout="centered")

width, height = 1500, 1500
max_height = 300
min_height = 3
R_core = 5
center_big = (width/2, height/2)
r_big = 564
r_small = 126
centers_small = [(width/4, height/4), (3*width/4, height/4), 
                 (width/4, 3*height/4), (3*width/4, 3*height/4)]

area_big_circle = math.pi * (r_big**2)
area_small_circles = 4 * (math.pi * (r_small**2))
L_transsect = math.sqrt(width**2 + height**2)

species_colors = {
    'KTT': '#1f77b4', 'Gy': '#2ca02c', 'MJ': '#ff7f0e', 'MCs': '#d62728', 'BaBe': '#9467bd'
}

def point_line_distance(x, y, x1, y1, x2, y2):
    num = abs((x2 - x1) * (y1 - y) - (x1 - x) * (y2 - y1))
    den = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return num / den

# STABILABB: Átlag számítása súlyozva (Transzekthez) vagy anélkül
def get_weighted_height_mean(df_subset, is_transzekt=False):
    if len(df_subset) == 0: return 0
    if is_transzekt:
        # Horvitz-Thompson korrekció az átlaghoz: sum(h * 1/h) / sum(1/h) = n / sum(1/h)
        return len(df_subset) / (1 / df_subset['height']).sum()
    else:
        return df_subset['height'].mean()

# --- 2. SZIMULÁCIÓS FÜGGVÉNY ---
def run_forest_simulation(params):
    target_intensity = params['intensity']
    grav_str = params['grav_str']
    n_grav = params['n_grav']
    
    # 1. Cél darabszám
    expected_n = int(target_intensity * width * height)
    N_target = np.random.poisson(expected_n)
    
    # 2. DINAMIKUS POOL: Minél nagyobb a gravitáció, annál több "nyers" pont kell
    # Erős csomósodásnál a pontok 90%-a is kieshet az R_core miatt a zsúfoltságban
    multiplier = 2 + (grav_str * 2) # 0-ás erőnél 2x, 10-esnél 22x túlbiztosítás
    N_pool = int(N_target * multiplier) + 500
    
    x_tmp = np.random.uniform(0, width, N_pool)
    y_tmp = np.random.uniform(0, height, N_pool)
    
    # 3. Gravitációs súlyok
    grav_centers = np.random.uniform(0, width, (n_grav, 2))
    dist_all = np.array([np.sqrt((x_tmp - cx)**2 + (y_tmp - cy)**2) for cx, cy in grav_centers])
    min_dists = dist_all.min(axis=0)
    
    weights = np.exp(-min_dists**2 / (2 * 400**2)) 
    weights = weights ** max(grav_str, 0.1)
    weights /= weights.max()
    
    # 4. Súlyozott elfogadás
    mask = np.random.uniform(0, 1, N_pool) < weights
    accepted = np.column_stack((x_tmp[mask], y_tmp[mask]))
    
    # 5. R_CORE SZŰRÉS (Optimalizáltabb maszkolással)
    final_keep = np.ones(len(accepted), dtype=bool)
    R_sq = R_core**2
    for i in range(len(accepted)):
        if not final_keep[i]: continue
        # Csak a még élő pontokat nézzük
        d_sq = np.sum((accepted[i] - accepted[i+1:])**2, axis=1)
        final_keep[i+1:][d_sq < R_sq] = False
    
    valid_coords = accepted[final_keep]
    
    # 6. VÉGSŐ LÉTSZÁM BEÁLLÍTÁSA
    # Ha a durva szűrés után is több maradt, levágjuk a felesleget
    if len(valid_coords) > N_target:
        idx = np.random.choice(len(valid_coords), N_target, replace=False)
        final_coords = valid_coords[idx]
    else:
        # Ha még így is kevés, akkor sajnos fizikai korlátba ütköztünk (nem fér el több fa)
        final_coords = valid_coords
        # Opcionális: jelezzük a usernek, ha nem sikerült elérni a célt
        # st.warning(f"Limit: Csak {len(final_coords)} fa fért el a sűrűsödési foltokban!")

    N_final = len(final_coords)
  # === GOOGLE SHEETS KAPCSOLAT ===
@st.cache_resource
def get_gsheets_connection():
    return st.connection("gsheets", type=GSheetsConnection)

# === SIDEBAR BEÁLLÍTÁSOK ===
with st.sidebar:
    st.header("⚙️ Beállítások")
    in_intensity = st.slider("Cél sűrűség (db/cm²)", 0.00005, 0.005, 0.0020, step=0.00005, format="%.5f")
    in_mode = st.slider("Leggyakoribb magasság (módusz)", 5, 50, 15)
    in_shape = st.slider("Változatosság (alacsonyabb = több óriás fa)", 1.2, 5.0, 2.0)
    in_grav_str = st.slider("Sűrűsödési erő", 0, 10, 3)
    in_grav_points = st.slider("Sűrűsödési pontok száma", 1, 5, 3)
    in_chewed = st.slider("Valódi rágottság (%)", 0, 100, 30)
    in_runs = st.slider("Szimulációs futások száma", 2, 100, 5)

    # Fafaj százalékok
    if 'KTT' not in st.session_state: st.session_state['KTT'] = 20
    p_ktt = st.slider("Kocsánytalan Tölgy (%)", 0, 100, key='KTT')
    p_gy = st.slider("Gyertyán (%)", 0, 100, key='Gy')
    p_mj = st.slider("Mezei Juhar (%)", 0, 100, key='MJ')
    p_mcs = st.slider("Madárcseresznye (%)", 0, 100, key='MCs')
    p_babe = max(0, 100 - (p_ktt + p_gy + p_mj + p_mcs))
    st.info(f"Barkóca Berkenye (maradék): {p_babe}%")

# === SZIMULÁCIÓ GOMB === (EZ A HIÁNYZÓ RÉSZ!)
if st.button("🚀 SZIMULÁCIÓ FUTTATÁSA", use_container_width=True):
    raw_probs = np.array([p_ktt, p_gy, p_mj, p_mcs, p_babe], dtype=float)
    corrected_probs = raw_probs / raw_probs.sum()

    sim_params = {
        'intensity': in_intensity, 'mode': in_mode, 'shape_k': in_shape, 
        'grav_str': in_grav_str, 'chewed_p': in_chewed/100,
        'n_grav': in_grav_points, 'sp_names': ['KTT', 'Gy', 'MJ', 'MCs', 'BaBe'],
        'sp_probs': corrected_probs 
    }

    all_runs_errors = []
    s_work = t_work = c_work = 0  # Inicializálás
    
    my_bar = st.progress(0, text="Szimulációk futtatása...")

    for i in range(in_runs):
        current_df = run_forest_simulation(sim_params)
        t_df = current_df[current_df['T'] == 1]
        c_df = current_df[current_df['C'] == 1]
        
        # VALÓDI ÉRTÉKEK
        s_dens = len(current_df) / (width * height)
        s_height_avg = get_weighted_height_mean(current_df)
        s_chew = current_df['chewed'].mean() * 100

        # TRANSZEKT
        if len(t_df) > 0:
            t_density = (1 / (2.0 * t_df['height'] * L_transsect)).sum()
            t_height_avg = get_weighted_height_mean(t_df, is_transzekt=True)
            t_chew = t_df['chewed'].mean() * 100
        else:
            t_density = t_height_avg = t_chew = 0.0
        
        # MINTAKÖR
        c_small = c_df[c_df['height'] <= 50]
        c_large = c_df[c_df['height'] > 50]
        d_small = (len(c_small) / area_small_circles) if area_small_circles > 0 else 0
        d_big = (len(c_large) / area_big_circle) if area_big_circle > 0 else 0
        c_dens = d_small + d_big
        
        if c_dens > 0 and (len(c_small) > 0 or len(c_large) > 0):
            avg_h_small = c_small['height'].mean() if len(c_small) > 0 else 0
            avg_h_large = c_large['height'].mean() if len(c_large) > 0 else 0
            avg_chew_small = c_small['chewed'].mean() if len(c_small) > 0 else 0
            avg_chew_large = c_large['chewed'].mean() if len(c_large) > 0 else 0
            c_height_avg = (d_small * avg_h_small + d_big * avg_h_large) / c_dens
            c_chew = ((d_small * avg_chew_small + d_big * avg_chew_large) / c_dens) * 100
        else:
            c_height_avg = c_chew = 0

        # Munkaidő (első futás alapján)
        s_work = (len(current_df) * 3.4) / 60
        t_work = (len(t_df) * 3.4) / 60
        c_work = (len(c_df) * 3.4) / 60

        # MAPE
        all_runs_errors.append({
            't_err_dens': abs((s_dens - t_density) / s_dens) if s_dens > 0 else 0,
            't_err_height': abs((s_height_avg - t_height_avg) / s_height_avg) if s_height_avg > 0 else 0,
            't_err_chew': abs((s_chew - t_chew) / s_chew) if s_chew > 0 else 0,
            'c_err_dens': abs((s_dens - c_dens) / s_dens) if s_dens > 0 else 0,
            'c_err_height': abs((s_height_avg - c_height_avg) / s_height_avg) if s_height_avg > 0 else 0,
            'c_err_chew': abs((s_chew - c_chew) / s_chew) if s_chew > 0 else 0
        })
        my_bar.progress((i + 1) / in_runs)

    # **HIBAJAVÍTÁS: errors_df létrehozása**
    errors_df = pd.DataFrame(all_runs_errors)
    my_bar.empty()

    # GOOGLE SHEETS MENTÉS
    try:
        conn = get_gsheets_connection()
        existing_data = conn.read()
        new_id = 1 if len(existing_data) == 0 else int(existing_data['ID'].max()) + 1
        
        avg_mape = {
            't_dens': errors_df['t_err_dens'].mean()*100,
            't_height': errors_df['t_err_height'].mean()*100,
            't_chew': errors_df['t_err_chew'].mean()*100,
            'c_dens': errors_df['c_err_dens'].mean()*100,
            'c_height': errors_df['c_err_height'].mean()*100,
            'c_chew': errors_df['c_err_chew'].mean()*100
        }
        
        sheet_row = {
            'ID': new_id, 'Dátum': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Sűrűség': in_intensity, 'Módusz': in_mode, 'Shape': in_shape,
            'Gravitáció': in_grav_str, 'Grav_pontok': in_grav_points, 'Rágottság_%': in_chewed,
            'Futások': in_runs, 'KTT_%': p_ktt, 'Gy_%': p_gy, 'MJ_%': p_mj, 
            'MCs_%': p_mcs, 'BaBe_%': p_babe,
            'T_Dens_MAPE': avg_mape['t_dens'], 'T_Height_MAPE': avg_mape['t_height'],
            'T_Chew_MAPE': avg_mape['t_chew'], 'C_Dens_MAPE': avg_mape['c_dens'],
            'C_Height_MAPE': avg_mape['c_height'], 'C_Chew_MAPE': avg_mape['c_chew'],
            'S_Munka_percek': s_work, 'T_Munka_percek': t_work, 'C_Munka_percek': c_work
        }
        
        conn.update(data=pd.DataFrame([sheet_row]))
        st.success(f"✅ Mentve! Sorszám: **{new_id}**")
    except Exception as e:
        st.error(f"❌ Sheets hiba: {e}")

    # MAPE TÁBLÁZAT
    st.subheader(f"📈 MAPE eredmények ({in_runs} futás)")
    mape_table = {
        "Sorok": ["Sűrűség", "Magasság", "Rágottság"],
        "Transzekt (T)": [
            f"{errors_df['t_err_dens'].mean()*100:.2f}%", 
            f"{errors_df['t_err_height'].mean()*100:.2f}%", 
            f"{errors_df['t_err_chew'].mean()*100:.2f}%"
        ],
        "Mintakör (C)": [
            f"{errors_df['c_err_dens'].mean()*100:.2f}%", 
            f"{errors_df['c_err_height'].mean()*100:.2f}%", 
            f"{errors_df['c_err_chew'].mean()*100:.2f}%"
        ]
    }
    st.table(pd.DataFrame(mape_table))
    st.info(f"**Munkaidő:** S: {s_work:.1f} | T: {t_work:.1f} | C: {c_work:.1f} perc")

