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
# --- 3. FELHASZNÁLÓI FELÜLET ---
st.title("🌲 Monitoring módszerek tesztelése szimulált környezetben")
# Ellenőrizzük, van-e már mentett szimulációnk
if 'forest_data' not in st.session_state:
    st.session_state['forest_data'] = None

# Rövid bemutatkozó szöveg
st.markdown("""
Ez a szimulátor egy virtuális újulat csoportot generál, ahol a Transzektes és Mintakörös vadhatás monitoring módszereket tesztelheted. 
A modell figyelembe veszi a fák egyedsűrűségét, magasságát a rágottságot és a fafaj-összetételt is, majd összehasonlítja felvételi módszerek becsült értékeit a szimuláció valós értékeivel.
* A két monitoring módszer rövid leírása:
* **Transzekt:** Egy vonal mentén azokat az egyedeket veszi fel amik legalább olyan magasak mint amilyen messze vannak a felvétel vonalától
* **Mintakör:** Egy nagy és négy kis kör van elhelyezve a területen. A nagy kör az 50cm-es vagy annál magasabb egyedeket feszi fel, a kis körök pedig azokat amik 50cm-nél kissebbek.
""")

# Lenyíló fül a magyarázatoknak
with st.expander("ℹ️ Hogyan működnek a beállítások?"):
    st.write("""
    * **Cél sűrűség:** Meghatározza, hogy átlagosan hány egyedet hozzon létre a program egységnyi területen.
    * **Leggyakoribb magasság:** Azt a magassági csoportot határozza meg amelyben a legtöbb egyed tartozik. (módusz).
    * **Változatosság (Shape):** Az egyedek magasság szerkezetét szabályozza. Az alacsony érték nagy méret beli szórást jelent, a magasabb érték pedig egységes magasságokat alacsony szórással. .
    * **Sűrűsödési erő (Csomósodás):** A fák csoportosulását szabályozza.
        * *Alacsony (0):* Egyenletes eloszlás.
        * *Magas (10):* Erős foltosság, a fák csoportokba tömörülnek.
    * **Valódi rágottság:** A vadkár mértéke a teljes állományban százalékban.
    * **Fafajok (%):** Az egyes fafajok előfordulási esélyét állíthatod be.
    * **Szimulációs futások:** Több futás esetén pontosabb átlagos hiba (MAPE) számítható.
    * **Figyelem!⚠️:** Magas egyedsűrűségnél és nagy futásszámnál a futási idő jelentősen megnő.
    """)

with st.sidebar:
    st.header("⚙️ Beállítások")
    in_intensity = st.slider("Cél sűrűség (db/cm²)", 0.00005, 0.005, 0.0020, step=0.00005, format="%.5f")
    
    # ÚJ CSÚSZKÁK A KAVARODÁS ELLEN
    in_mode = st.slider("Leggyakoribb magasság (módusz)", 5, 50, 15)
    in_shape = st.slider("Változatosság (alacsonyabb = több óriás fa)", 1.2, 5.0, 2.0)
    
    in_grav_str = st.slider("Sűrűsödési erő", 0, 10, 3)
    in_grav_points = st.slider("Sűrűsödési pontok száma", 1, 5, 3)
    in_chewed = st.slider("Valódi rágottság (%)", 0, 100, 30)
    in_runs = 100 
    st.sidebar.info(f"Mód: Adatgyűjtés (Fix {in_runs} futás)")

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
    st.info(f"Barkóca Berkenye (maradék): {p_babe}%")
    st.sidebar.markdown("---")
    st.sidebar.caption("**Készítette:**")
    st.sidebar.info(" Skultéty Fülöp skultetymfulop@gmail.com")

# --- EZ AZ ÚJ ADATGYŰJTŐ BLOKK ---
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
    progress_bar = st.progress(0, text="Adatgyűjtés folyamatban (100 futás)...")

    for i in range(100):
        current_df = run_forest_simulation(sim_params)
        
        # Alapértékek
        s_dens = len(current_df) / (width * height)
        s_height_avg = get_weighted_height_mean(current_df)
        s_chew = current_df['chewed'].mean() * 100

        # Módszerek becslései (T és C rövidítve a helytakarékosság miatt)
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

        # Hibák gyűjtése
        all_runs_errors.append({
            'err_dens_T': abs(s_dens - t_dens) / s_dens if s_dens > 0 else 0,
            'err_chew_T': abs(s_chew - t_chew) / s_chew if s_chew > 0 else 0,
            'err_dens_C': abs(s_dens - c_dens) / s_dens if s_dens > 0 else 0,
            'err_chew_C': abs(s_chew - c_chew) / s_chew if s_chew > 0 else 0
        })
        if i % 10 == 0: progress_bar.progress((i + 1) / 100)

    progress_bar.empty()
    res_df = pd.DataFrame(all_runs_errors)

    # Eredmény sor összeállítása
    summary_row = {
        "Dátum": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "In_Sűrűség": f"{in_intensity:.5f}",
        "In_Csomósodás": in_grav_str,
        "In_Rágottság": in_chewed,
        "MAPE_Sűrűség_T (%)": res_df['err_dens_T'].mean() * 100,
        "MAPE_Rágottság_T (%)": res_df['err_chew_T'].mean() * 100,
        "MAPE_Sűrűség_C (%)": res_df['err_dens_C'].mean() * 100,
        "MAPE_Rágottság_C (%)": res_df['err_chew_C'].mean() * 100
    }

    st.subheader("📋 Összesített mérési eredmény (100 futás átlaga)")
    st.dataframe(pd.DataFrame([summary_row]))
  # --- GOOGLE SHEETS MENTÉS ---
    try:
        # Kapcsolat létrehozása
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # A jelenlegi adatok beolvasása a táblázatból
        # (Fontos: a worksheet neve egyezzen a táblázat fülének nevével, pl. "Sheet1")
        existing_data = conn.read(worksheet="Sheet1", ttl=0)
        
        # Az új sor hozzáadása a meglévőkhöz
        new_row_df = pd.DataFrame([summary_row])
        updated_df = pd.concat([existing_data, new_row_df], ignore_index=True)
        
        # A teljes táblázat frissítése az új sorral
        conn.update(worksheet="Sheet1", data=updated_df)
        
        st.success("✅ Az adatok automatikusan mentve a Google Táblázatba!")
    except Exception as e:
        st.warning(f"⚠️ Megjelenítés sikerült, de a Google Sheets mentésnél hiba történt: {e}")
        st.info("Ellenőrizd, hogy a Google Táblázatod fülének neve 'Sheet1'-e, és a Megosztás beállításnál 'Szerkesztő' jogot adtál-e bárkinek, aki rendelkezik a linkkel.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Magasság eloszlás")
        fig_dist, ax_dist = plt.subplots()
        sns.histplot(df['height'], kde=True, bins=int(max_height / 5), color="forestgreen", ax=ax_dist)
        st.pyplot(fig_dist)
        plt.close(fig_dist)

    with col2:
        st.subheader("🧊 Interaktív 3D Erdő")
        view_option = st.radio(
            "Nézet kiválasztása:",
            ["Alap (Fafajok)", "Transzekt (Mért egyedek)", "Mintakörök (Mért egyedek)", "Vadkár (Rágott egyedek)"],
            horizontal=True, key="3d_view_selector"
        )
        
        # 1. ADATOK ÉS SZÍNEK ELŐKÉSZÍTÉSE
        plot_df = df.copy()
        color_map = species_colors
        color_col = 'species'

        if view_option == "Transzekt (Mért egyedek)":
            plot_df['status'] = plot_df['T'].map({1: 'Mért', 0: 'Kimaradt'})
            color_col, color_map = 'status', {'Mért': '#e74c3c', 'Kimaradt': '#bdc3c7'}
        elif view_option == "Mintakörök (Mért egyedek)":
            plot_df['status'] = plot_df['C'].map({1: 'Mért', 0: 'Kimaradt'})
            color_col, color_map = 'status', {'Mért': '#3498db', 'Kimaradt': '#bdc3c7'}
        elif view_option == "Vadkár (Rágott egyedek)":
            plot_df['status'] = plot_df['chewed'].map({1: 'Rágott', 0: 'Ép'})
            color_col, color_map = 'status', {'Rágott': '#f1c40f', 'Ép': '#2ecc71'}

        # 2. AZ ALAP ÁBRA LÉTREHOZÁSA (A PONTOKKAL)
        fig_3d = px.scatter_3d(plot_df, x='X', y='Y', z='height', color=color_col, 
                               color_discrete_map=color_map, opacity=0.7)
        
        # 3. EXTRA RÉTEGEK HOZZÁADÁSA (MÁR A LÉTEZŐ fig_3d-hez)
        if view_option == "Transzekt (Mért egyedek)":
            fig_3d.add_scatter3d(x=[0, width], y=[0, height], z=[0, 0], 
                                 mode='lines', line=dict(color='red', width=5), name="Vonal")
        
        elif view_option == "Mintakörök (Mért egyedek)":
            t = np.linspace(0, 2*np.pi, 50)
            # Nagy kör
            fig_3d.add_scatter3d(x=center_big[0] + r_big * np.cos(t), 
                                 y=center_big[1] + r_big * np.sin(t), 
                                 z=[0]*50, mode='lines', 
                                 line=dict(color='navy', width=4), name="Nagy kör")
            # A 4 kis kör ciklussal
            for i, cs in enumerate(centers_small):
                fig_3d.add_scatter3d(x=cs[0] + r_small * np.cos(t), 
                                     y=cs[1] + r_small * np.sin(t), 
                                     z=[0]*50, mode='lines', 
                                     line=dict(color='dodgerblue', width=3), name=f"{i+1}. kis kör")

        # 4. MEGJELENÍTÉSI BEÁLLÍTÁSOK
        fig_3d.update_traces(marker=dict(size=2))
        fig_3d.update_layout(margin=dict(l=0, r=0, b=0, t=0), scene_zaxis_range=[0, 1500])
        st.plotly_chart(fig_3d, use_container_width=True)
    # Térképek és rágottság
    st.subheader("🗺️ Mintavételi térképek")
    m1, m2 = st.columns(2)
    with m1:
        st.write("Transzekt")
        fig_map, ax_map = plt.subplots()
        ax_map.scatter(df['X'], df['Y'], c='lightgrey', s=2, alpha=0.3)
        t_df_plot = df[df['T'] == 1]
        ax_map.scatter(t_df_plot['X'], t_df_plot['Y'], c='red', s=10)
        ax_map.plot([0, width], [0, height], 'r--', lw=1)
        ax_map.set_aspect('equal')
        st.pyplot(fig_map)
    with m2:
        st.write("Mintakörök")
        fig_circ, ax_circ = plt.subplots()
        ax_circ.scatter(df['X'], df['Y'], c='lightgrey', s=2, alpha=0.3)
        c_df_plot = df[df['C'] == 1]
        ax_circ.scatter(c_df_plot['X'], c_df_plot['Y'], c='blue', s=10)
        ax_circ.add_patch(patches.Circle(center_big, r_big, color='navy', fill=False))
        for cs in centers_small: ax_circ.add_patch(patches.Circle(cs, r_small, color='dodgerblue', fill=False))
        ax_circ.set_aspect('equal')
        st.pyplot(fig_circ)

   

    st.subheader("🦌 Rágottság fafajonkénti összehasonlítása")
    
    # Adatok előkészítése
    species_list = d['sp_list']
    
    # 1. Valódi (S)
    s_chew_data = df.groupby('species')['chewed'].mean() * 100
    # 2. Transzekt (T)
    t_df = df[df['T'] == 1]
    t_chew_data = t_df.groupby('species')['chewed'].mean() * 100
    # 3. Mintakör (C)
    c_df = df[df['C'] == 1]
    c_chew_data = c_df.groupby('species')['chewed'].mean() * 100

    # Adatkeretbe rendezzük a könnyebb rajzolás érdekében
    plot_data = []
    for sp in species_list:
        plot_data.append({'Fafaj': sp, 'Típus': 'Valódi (S)', 'Rágottság %': s_chew_data.get(sp, 0)})
        plot_data.append({'Fafaj': sp, 'Típus': 'Transzekt (T)', 'Rágottság %': t_chew_data.get(sp, 0)})
        plot_data.append({'Fafaj': sp, 'Típus': 'Mintakör (C)', 'Rágottság %': c_chew_data.get(sp, 0)})
    
    chew_compare_df = pd.DataFrame(plot_data)

    # Diagram elkészítése
    fig_chew, ax_chew = plt.subplots(figsize=(12, 5))
    
    # Csoportosított oszlopdiagram Seaborn-nal
    sns.barplot(
        data=chew_compare_df, 
        x='Fafaj', 
        y='Rágottság %', 
        hue='Típus', 
        palette={'Valódi (S)': '#2ecc71', 'Transzekt (T)': '#e74c3c', 'Mintakör (C)': '#3498db'},
        ax=ax_chew
    )

    # Vízszintes vonal az összesített beállított célértékhez
    ax_chew.axhline(d['in_chewed'], color='black', linestyle='--', alpha=0.5, label='Beállított cél %')
    
    ax_chew.set_ylim(0, 100)
    ax_chew.set_ylabel("Rágottság (%)")
    ax_chew.grid(axis='y', linestyle=':', alpha=0.7)
    ax_chew.legend()
    
    st.pyplot(fig_chew)





