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

    
  # --- TERÜLETILEG SÚLYOZOTT MAGASSÁG ---
    shape_k = params['shape_k']
    target_mode = params['mode']
    theta = target_mode / (shape_k - 1) if shape_k > 1 else target_mode
    
    # 1. Alap magasságok generálása
    raw_heights = np.random.gamma(shape=shape_k, scale=theta, size=N_final)
    raw_heights = np.clip(raw_heights, min_height, max_height)
    raw_heights.sort() 

    # 2. Helyi "vonzóerő" (final_attraction) kiszámítása
    if n_grav > 0 and grav_str > 0:
        final_dist_all = np.array([np.sqrt((final_coords[:,0] - cx)**2 + (final_coords[:,1] - cy)**2) for cx, cy in grav_centers])
        final_min_dists = final_dist_all.min(axis=0)
        
        attraction_base = np.exp(-final_min_dists**2 / (2 * 200**2))
        noise = np.random.normal(0, 0.15, N_final)
        
        # Ez a változó kapja meg az értékeket
        final_attraction = (attraction_base * (grav_str / 10)) + noise
    else:
        # Ha nincs gravitáció, tiszta véletlen
        final_attraction = np.random.rand(N_final)

    # 3. Összepárosítás (Csak egyszer!)
    attraction_order = final_attraction.argsort() 
    heights = np.zeros(N_final)
    heights[attraction_order] = raw_heights

    # --- ADATOK ÖSSZEGYŰJTÉSE ---
    if N_final == 0:
        return pd.DataFrame(columns=["X", "Y", "height", "species", "chewed", "T", "C"])

    fajok = np.random.choice(params['sp_names'], size=N_final, p=params['sp_probs'])
    ragottsag = np.random.uniform(0, 100, size=N_final) < params['chewed_p']
    
    results = []
    for i in range(N_final):
        x, y, h = float(final_coords[i,0]), float(final_coords[i,1]), float(heights[i])
        
        # TRANSZEKT (T)
        d_line = point_line_distance(x, y, 0, 0, width, height)
        in_t = 1 if d_line <= h else 0
        
        # MINTAKÖR (C)
        in_c = 0
        dist_to_center = math.sqrt((x - center_big[0])**2 + (y - center_big[1])**2)
        if h > 50 and dist_to_center <= r_big: 
            in_c = 1
        elif h <= 50:
            for cs in centers_small:
                if math.sqrt((x - cs[0])**2 + (y - cs[1])**2) <= r_small: 
                    in_c = 1
                    break
        
        results.append({
            "X": x, "Y": y, "height": h, "species": fajok[i], 
            "chewed": int(ragottsag[i]), "T": in_t, "C": in_c
        })
    
    return pd.DataFrame(results)

    # Generáljuk a maradék adatokat
    fajok = np.random.choice(params['sp_names'], size=N_final, p=params['sp_probs'])
    ragottsag = np.random.uniform(0, 100, size=N_final) < params['chewed_p']
    
    results = []
    for i in range(N_final):
        x, y, h = float(final_coords[i,0]), float(final_coords[i,1]), float(heights[i])
        
        # TRANSZEKT (T): Távolság alapú számítás
        # A h (magasság) itt a sáv fél-szélessége!
        d_line = point_line_distance(x, y, 0, 0, width, height)
        in_t = 1 if d_line <= h else 0
        
        # MINTAKÖR (C)
        in_c = 0
        dist_to_center = math.sqrt((x - center_big[0])**2 + (y - center_big[1])**2)
        if h >= 50 and dist_to_center <= r_big: 
            in_c = 1
        elif h < 50:
            for cs in centers_small:
                if math.sqrt((x - cs[0])**2 + (y - cs[1])**2) <= r_small: 
                    in_c = 1
                    break
        
        results.append({
            "X": x, "Y": y, "height": h, "species": fajok[i], 
            "chewed": int(ragottsag[i]), "T": in_t, "C": in_c
        })
    
    return pd.DataFrame(results)
    # A IMPORT részt egészítsd ki EZZEL (a többi marad):
import streamlit as st
from streamlit_gsheets import GSheetsConnection  # ← EZT add hozzá!

# A run_forest_simulation FÜGGVÉNY után, a SZIMULÁCIÓ GOMB ELŐTT add ezt:
@st.cache_resource
def get_gsheets_connection():
    return st.connection("gsheets", type=GSheetsConnection)

# A "SZIMULÁCIÓ FUTTATÁSA" GOMB BELSEJÉBE (a my_bar.empty() UTÁN):
    my_bar.empty()

    # === GOOGLE SHEETS MENTÉS === (ÚJ!)
    try:
        conn = get_gsheets_connection()
        
        # Sorszám generálása (legnagyobb + 1)
        existing_data = conn.read()
        new_id = 1 if len(existing_data) == 0 else int(existing_data['ID'].max()) + 1
        
        # ÖSSZES MAPE ÁTLEG
        avg_mape = {
            't_dens': errors_df['t_err_dens'].mean()*100,
            't_height': errors_df['t_err_height'].mean()*100,
            't_chew': errors_df['t_err_chew'].mean()*100,
            'c_dens': errors_df['c_err_dens'].mean()*100,
            'c_height': errors_df['c_err_height'].mean()*100,
            'c_chew': errors_df['c_err_chew'].mean()*100
        }
        
        # MENTENDŐ SOR (slider paraméterek + MAPE + munkaidő)
        sheet_row = {
            'ID': new_id,
            'Dátum': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Sűrűség': f"{in_intensity:.5f}",
            'Módusz': in_mode,
            'Shape': in_shape,
            'Gravitáció': in_grav_str,
            'Grav_pontok': in_grav_points,
            'Rágottság_%': in_chewed,
            'Futások': in_runs,
            'KTT_%': p_ktt, 'Gy_%': p_gy, 'MJ_%': p_mj, 'MCs_%': p_mcs, 'BaBe_%': p_babe,
            # MAPE értékek
            'T_Dens_MAPE': f"{avg_mape['t_dens']:.2f}%",
            'T_Height_MAPE': f"{avg_mape['t_height']:.2f}%",
            'T_Chew_MAPE': f"{avg_mape['t_chew']:.2f}%",
            'C_Dens_MAPE': f"{avg_mape['c_dens']:.2f}%",
            'C_Height_MAPE': f"{avg_mape['c_height']:.2f}%",
            'C_Chew_MAPE': f"{avg_mape['c_chew']:.2f}%",
            # Munkaidő
            'S_Munka_percek': f"{s_work:.1f}",
            'T_Munka_percek': f"{t_work:.1f}",
            'C_Munka_percek': f"{c_work:.1f}"
        }
        
        # ÍRÁS A SHEETS-BE
        conn.update(data=pd.DataFrame([sheet_row]))
        st.success(f"✅ Adatok mentve! Sorszám: **{new_id}**")
        
    except Exception as e:
        st.error(f"❌ Sheets mentés hiba: {e}")

    # 1. LÉPÉS: Elmentjük az adatokat (session_state-be MÉG MINDIG)
    st.session_state['forest_data'] = {
        # ... meglévő adatok ...
    }
