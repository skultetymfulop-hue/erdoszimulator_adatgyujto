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
from streamlit_gsheets import GSheetsConnection

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

def get_weighted_height_mean(df_subset, is_transzekt=False):
    if len(df_subset) == 0: return 0
    if is_transzekt:
        return len(df_subset) / (1 / df_subset['height']).sum()
    else:
        return df_subset['height'].mean()

# --- 2. SZIMULÁCIÓS FÜGGVÉNY ---
def run_forest_simulation(params):
    target_intensity = params['intensity']
    grav_str = params['grav_str']
    n_grav = params['n_grav']
    
    expected_n = int(target_intensity * width * height)
    N_target = np.random.poisson(expected_n)
    
    multiplier = 2 + (grav_str * 2) 
    N_pool = int(N_target * multiplier) + 500
    
    x_tmp = np.random.uniform(0, width, N_pool)
    y_tmp = np.random.uniform(0, height, N_pool)
    
    grav_centers = np.random.uniform(0, width, (n_grav, 2))
    dist_all = np.array([np.sqrt((x_tmp - cx)**2 + (y_tmp - cy)**2) for cx, cy in grav_centers])
    min_dists = dist_all.min(axis=0)
    
    weights = np.exp(-min_dists**2 / (2 * 400**2)) 
    weights = weights ** max(grav_str, 0.1)
    weights /= weights.max()
    
    mask = np.random.uniform(0, 1, N_pool) < weights
    accepted = np.column_stack((x_tmp[mask], y_tmp[mask]))
    
    final_keep = np.ones(len(accepted), dtype=bool)
    R_sq = R_core**2
    for i in range(len(accepted)):
        if not final_keep[i]: continue
        d_sq = np.sum((accepted[i] - accepted[i+1:])**2, axis=1)
        final_keep[i+1:][d_sq < R_sq] = False
    
    valid_coords = accepted[final_keep]
    
    if len(valid_coords) > N_target:
        idx = np.random.choice(len(valid_coords), N_target, replace=False)
        final_coords = valid_coords[idx]
    else:
        final_coords = valid_coords

    N_final = len(final_coords)
    
    shape_k = params['shape_k']
    target_mode = params['mode']
    theta = target_mode / (shape_k - 1) if shape_k > 1 else target_mode
    
    raw_heights = np.random.gamma(shape=shape_k, scale=theta, size=N_final)
    raw_heights = np.clip(raw_heights, min_height, max_height)
    raw_heights.sort() 

    if n_grav > 0 and grav_str > 0:
        final_dist_all = np.array([np.sqrt((final_coords[:,0] - cx)**2 + (final_coords[:,1] - cy)**2) for cx, cy in grav_centers])
        final_min_dists = final_dist_all.min(axis=0)
        attraction_base = np.exp(-final_min_dists**2 / (2 * 200**2))
        noise = np.random.normal(0, 0.15, N_final)
        final_attraction = (attraction_base * (grav_str / 10)) + noise
    else:
        final_attraction = np.random.rand(N_final)

    attraction_order = final_attraction.argsort() 
    heights = np.zeros(N_final)
    heights[attraction_order] = raw_heights

    if N_final == 0:
        return pd.DataFrame(columns=["X", "Y", "height", "species", "chewed", "T", "C"])

    fajok = np.random.choice(params['sp_names'], size=N_final, p=params['sp_probs'])
    ragottsag = np.random.uniform(0, 100, size=N_final) < params['chewed_p']
    
    results = []
    for i in range(N_final):
        x, y, h = float(final_coords[i,0]), float(final_coords[i,1]), float(heights[i])
        d_line = point_line_distance(x, y, 0, 0, width, height)
        in_t = 1 if d_line <= h else 0
        
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

# --- 3. FELHASZNÁLÓI FELÜLET ---
st.title("🌲 Monitoring módszerek tesztelése szimulált környezetben")

if 'forest_data' not in st.session_state:
    st.session_state['forest_data'] = None

st.markdown("""
Ez a szimulátor egy virtuális újulat csoportot generál, ahol a Transzektes és Mintakörös vadhatás monitoring módszereket tesztelheted. 
... (leírás folytatódik)
""")

with st.expander("ℹ️ Hogyan működnek a beállítások?"):
    st.write("...")

with st.sidebar:
    st.header("⚙️ Beállítások")
    in_intensity = st.slider("Cél sűrűség (db/cm²)", 0.00005, 0.005, 0.0020, step=0.00005, format="%.5f")
    in_mode = st.slider("Leggyakoribb magasság (módusz)", 5, 50, 15)
    in_shape = st.slider("Változatosság (alacsonyabb = több óriás fa)", 1.2, 5.0, 2.0)
    in_grav_str = st.slider("Sűrűsödési erő", 0, 10, 3)
    in_grav_points = st.slider("Sűrűsödési pontok száma", 1, 5, 3)
    in_chewed = st.slider("Valódi rágottság (%)", 0, 100, 30)
    in_runs = 100 

    if 'KTT' not in st.session_state: st.session_state['KTT'] = 20
    if 'Gy' not in st.session_state: st.session_state['Gy'] = 20
    if 'MJ' not in st.session_state: st.session_state['MJ'] = 20
    if 'MCs' not in st.session_state: st.session_state['MCs'] = 20

    def sync_sliders(changed_key):
        current_total = st.session_state['KTT'] + st.session_state['Gy'] + st.session_state['MJ'] + st.session_state['MCs']
        if current_total > 100:
            excess = current_total - 100
            others = [k for k in ['KTT', 'Gy', 'MJ', 'MCs'] if k != changed_key]
            for k in others:
                if st.session_state[k] >= excess:
                    st.session_state[k] -= excess
                    excess = 0
                    break
                else:
                    excess -= st.session_state[k]
                    st.session_state[k] = 0

    p_ktt = st.slider("Kocsánytalan Tölgy (%)", 0, 100, key='KTT', on_change=sync_sliders, args=('KTT',))
    p_gy = st.slider("Gyertyán (%)", 0, 100, key='Gy', on_change=sync_sliders, args=('Gy',))
    p_mj = st.slider("Mezei Juhar (%)", 0, 100, key='MJ', on_change=sync_sliders, args=('MJ',))
    p_mcs = st.slider("Madárcseresznye (%)", 0, 100, key='MCs', on_change=sync_sliders, args=('MCs',))
    p_babe = max(0, 100 - (p_ktt + p_gy + p_mj + p_mcs))

# --- ADATGYŰJTŐ ÉS MENTŐ BLOKK ---
if st.button("100 SZIMULÁCIÓ FUTTATÁSA ÉS ÖSSZESÍTÉSE", use_container_width=True):
    raw_probs = np.array([p_ktt, p_gy, p_mj, p_mcs, p_babe], dtype=float)
    corrected_probs = raw_probs / raw_probs.sum()

    sim_params = {
        'intensity': in_intensity, 'mode': in_mode, 'shape_k': in_shape, 'grav_str': in_grav_str,
        'chewed_p': in_chewed, 'n_grav': in_grav_points,
        'sp_names': ['KTT', 'Gy', 'MJ', 'MCs', 'BaBe'],
        'sp_probs': corrected_probs 
    }

    all_runs_errors = []
    progress_bar = st.progress(0, text="Adatgyűjtés folyamatban...")

    for i in range(100):
        current_df = run_forest_simulation(sim_params)
        s_dens = len(current_df) / (width * height)
        s_chew = current_df['chewed'].mean() * 100
        t_df = current_df[current_df['T'] == 1]
        t_dens = (1 / (2.0 * t_df['height'] * L_transsect)).sum() if len(t_df)>0 else 0
        t_chew = t_df['chewed'].mean() * 100 if len(t_df)>0 else 0
        c_df = current_df[current_df['C'] == 1]
        c_small = c_df[c_df['height'] <= 50]
        c_large = c_df[c_df['height'] > 50]
        d_s = (len(c_small) / area_small_circles) if area_small_circles > 0 else 0
        d_l = (len(c_large) / area_big_circle) if area_big_circle > 0 else 0
        c_dens = d_s + d_l
        c_chew = (((d_s * c_small['chewed'].mean() if len(c_small)>0 else 0) + 
                   (d_l * c_large['chewed'].mean() if len(c_large)>0 else 0)) / c_dens * 100) if c_dens > 0 else 0

        all_runs_errors.append({
            'err_dens_T': abs(s_dens - t_dens) / s_dens if s_dens > 0 else 0,
            'err_chew_T': abs(s_chew - t_chew) / s_chew if s_chew > 0 else 0,
            'err_dens_C': abs(s_dens - c_dens) / s_dens if s_dens > 0 else 0,
            'err_chew_C': abs(s_chew - c_chew) / s_chew if s_chew > 0 else 0
        })
        if i % 10 == 0: progress_bar.progress((i + 1) / 100)

    progress_bar.empty()
    res_df = pd.DataFrame(all_runs_errors)

    summary_row = {
        "In_Sűrűség": f"{in_intensity:.5f}",
        "In_Csomósodás": int(in_grav_str),
        "In_Rágottság": int(in_chewed),
        "MAPE_Sűrűség_T (%)": round(float(res_df['err_dens_T'].mean() * 100), 2),
        "MAPE_Rágottság_T (%)": round(float(res_df['err_chew_T'].mean() * 100), 2),
        "MAPE_Sűrűség_C (%)": round(float(res_df['err_dens_C'].mean() * 100), 2),
        "MAPE_Rágottság_C (%)": round(float(res_df['err_chew_C'].mean() * 100), 2)
    }

    st.subheader("📋 Összesített mérési eredmény")
    st.dataframe(pd.DataFrame([summary_row]))

    # --- GOOGLE SHEETS MENTÉS (Most már az IF blokkon BELÜL van!) ---
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        target_sheet = "Sheet1"
        
        try:
            existing_data = conn.read(worksheet=target_sheet, ttl=0)
        except Exception:
            existing_data = pd.DataFrame()

        if not existing_data.empty and "ID" in existing_data.columns:
            last_id = pd.to_numeric(existing_data["ID"]).max()
            new_id = int(last_id + 1) if not np.isnan(last_id) else 1
        else:
            new_id = 1

        summary_row["ID"] = new_id  # Hozzáadjuk az ID-t a mentés előtt
        
        new_row_df = pd.DataFrame([summary_row])
        updated_df = pd.concat([existing_data, new_row_df], ignore_index=True)
        
        conn.update(worksheet=target_sheet, data=updated_df)
        st.success(f"✅ Mentve! Új sorszám: {new_id}")

    except Exception as e:
        st.error(f"Hiba történt a sorszámozott mentésnél: {e}")
