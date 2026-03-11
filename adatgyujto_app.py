import streamlit as st
import numpy as np
import pandas as pd
import math

# --- 1. ALAPBEÁLLÍTÁSOK ---
st.set_page_config(page_title="MAPE Szimulátor", layout="centered")

width, height = 1500, 1500
R_core = 5
center_big = (width/2, height/2)
r_big, r_small = 564, 126
centers_small = [(width/4, height/4), (3*width/4, height/4), (width/4, 3*height/4), (3*width/4, 3*height/4)]
area_big_circle = math.pi * (r_big**2)
area_small_circles = 4 * (math.pi * (r_small**2))
L_transsect = math.sqrt(width**2 + height**2)

def point_line_distance(x, y, x1, y1, x2, y2):
    num = abs((x2 - x1) * (y1 - y) - (x1 - x) * (y2 - y1))
    den = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return num / den

def get_weighted_height_mean(df_subset, is_transzekt=False):
    if len(df_subset) == 0: return 0
    if is_transzekt:
        return len(df_subset) / (1 / df_subset['height']).sum()
    return df_subset['height'].mean()

# --- 2. SZIMULÁCIÓS MOTOR ---
def run_forest_simulation(params):
    expected_n = int(params['intensity'] * width * height)
    N_target = np.random.poisson(expected_n)
    N_pool = int(N_target * (2 + params['grav_str'] * 2)) + 500
    
    x_tmp, y_tmp = np.random.uniform(0, width, N_pool), np.random.uniform(0, height, N_pool)
    grav_centers = np.random.uniform(0, width, (params['n_grav'], 2))
    min_dists = np.array([np.sqrt((x_tmp - cx)**2 + (y_tmp - cy)**2) for cx, cy in grav_centers]).min(axis=0)
    
    weights = np.exp(-min_dists**2 / (2 * 400**2)) ** max(params['grav_str'], 0.1)
    mask = np.random.uniform(0, 1, N_pool) < (weights / weights.max())
    accepted = np.column_stack((x_tmp[mask], y_tmp[mask]))
    
    final_keep = np.ones(len(accepted), dtype=bool)
    for i in range(len(accepted)):
        if not final_keep[i]: continue
        d_sq = np.sum((accepted[i] - accepted[i+1:])**2, axis=1)
        final_keep[i+1:][d_sq < R_core**2] = False
    
    coords = accepted[final_keep]
    if len(coords) > N_target: coords = coords[np.random.choice(len(coords), N_target, replace=False)]
    
    N = len(coords)
    shape_k, mode = params['shape_k'], params['mode']
    theta = mode / (shape_k - 1) if shape_k > 1 else mode
    heights = np.sort(np.clip(np.random.gamma(shape=shape_k, scale=theta, size=N), 3, 300))
    
    results = []
    for i in range(N):
        x, y, h = float(coords[i,0]), float(coords[i,1]), float(heights[i])
        in_t = 1 if point_line_distance(x, y, 0, 0, width, height) <= h else 0
        in_c = 0
        if (h >= 50 and math.sqrt((x-center_big[0])**2 + (y-center_big[1])**2) <= r_big) or \
           (h < 50 and any(math.sqrt((x-cs[0])**2 + (y-cs[1])**2) <= r_small for cs in centers_small)):
            in_c = 1
        results.append({"height": h, "chewed": int(np.random.rand() < params['chewed_p']/100), "T": in_t, "C": in_c})
    return pd.DataFrame(results)

# --- 3. UI ÉS LOGIKA ---
st.title("📊 Monitoring módszerek MAPE analízise")
st.markdown("A szimuláció 100 futás átlagolt hibáját (MAPE) számolja ki.")

with st.sidebar:
    st.header("⚙️ Beállítások")
    in_intensity = st.slider("Cél sűrűség", 0.0005, 0.005, 0.002, format="%.4f")
    in_mode = st.slider("Leggyakoribb magasság (módusz)", 5, 50, 15)
    in_shape = st.slider("Változatosság (Shape)", 1.2, 5.0, 2.0)
    in_grav_str = st.slider("Csomósodás ereje", 0, 10, 3)
    in_chewed = st.slider("Valódi rágottság (%)", 0, 100, 30)

if st.button("ANALÍZIS INDÍTÁSA", use_container_width=True):
    all_runs_errors = []
    my_bar = st.progress(0, text="Szimulációk futtatása...")

    for i in range(100):
        current_df = run_forest_simulation({
            'intensity': in_intensity, 'mode': in_mode, 'shape_k': in_shape, 
            'grav_str': in_grav_str, 'chewed_p': in_chewed, 'n_grav': 3
        })
        
        # Valódi értékek
        s_dens = len(current_df) / (width * height)
        s_height_avg = current_df['height'].mean()
        s_chew = current_df['chewed'].mean() * 100

        # Transzekt
        t_df = current_df[current_df['T'] == 1]
        t_density = (1 / (2.0 * t_df['height'] * L_transsect)).sum() if not t_df.empty else 0
        t_height_avg = get_weighted_height_mean(t_df, is_transzekt=True)
        t_chew = t_df['chewed'].mean() * 100 if not t_df.empty else 0
        
        # Mintakör
        c_df = current_df[current_df['C'] == 1]
        c_small = c_df[c_df['height'] <= 50]
        c_large = c_df[c_df['height'] > 50]
        d_small = (len(c_small) / area_small_circles) if area_small_circles > 0 else 0
        d_big = (len(c_large) / area_big_circle) if area_big_circle > 0 else 0
        c_dens = d_small + d_big
        
        if c_dens > 0:
            avg_h_s, avg_h_l = c_small['height'].mean() if not c_small.empty else 0, c_large['height'].mean() if not c_large.empty else 0
            avg_c_s, avg_c_l = c_small['chewed'].mean() if not c_small.empty else 0, c_large['chewed'].mean() if not c_large.empty else 0
            c_height_avg = (d_small * avg_h_s + d_big * avg_h_l) / c_dens
            c_chew = ((d_small * avg_c_s + d_big * avg_c_l) / c_dens) * 100
        else:
            c_height_avg = c_chew = 0

        all_runs_errors.append({
            't_err_dens': abs(s_dens - t_density) / s_dens if s_dens > 0 else 0,
            't_err_height': abs(s_height_avg - t_height_avg) / s_height_avg if s_height_avg > 0 else 0,
            't_err_chew': abs(s_chew - t_chew) / s_chew if s_chew > 0 else 0,
            'c_err_dens': abs(s_dens - c_dens) / s_dens if s_dens > 0 else 0,
            'c_err_height': abs(s_height_avg - c_height_avg) / s_height_avg if s_height_avg > 0 else 0,
            'c_err_chew': abs(s_chew - c_chew) / s_chew if s_chew > 0 else 0
        })
        my_bar.progress((i + 1) / 100)

    my_bar.empty()
    errors_df = pd.DataFrame(all_runs_errors)

    mape_table = {
        "Paraméter": ["Sűrűség (Density)", "Átlagmagasság (Height)", "Rágottság (Chewed)"],
        "Transzekt (T) MAPE": [
            f"{errors_df['t_err_dens'].mean()*100:.2f}%", 
            f"{errors_df['t_err_height'].mean()*100:.2f}%", 
            f"{errors_df['t_err_chew'].mean()*100:.2f}%"
        ],
        "Mintakör (C) MAPE": [
            f"{errors_df['c_err_dens'].mean()*100:.2f}%", 
            f"{errors_df['c_err_height'].mean()*100:.2f}%", 
            f"{errors_df['c_err_chew'].mean()*100:.2f}%"
        ]
    }

    st.subheader("📈 MAPE eredmények")
    st.table(pd.DataFrame(mape_table))
