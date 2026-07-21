import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- APP CONFIG ---
st.set_page_config(page_title="Naboom Nuut: Tactical Open", layout="wide")

# --- STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #FFFFFF; }
    .neon-text { color: #BFFF00; text-shadow: 0 0 10px #BFFF00; text-align: center; width: 100%; }
    [data-testid="stHorizontalBlock"] { align-items: center; }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE CONNECTION ---
# This connects to the URL you will put in your Streamlit Secrets (Phase 3)
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    return conn.read(ttl="5s") # Refreshes every 5 seconds

def save_data(df):
    conn.update(data=df)
    st.cache_data.clear()

# --- INITIALIZE TOURNAMENT DATA ---
players = ["Bennie", "Adriaan", "Danie", "Martin", "Frederik"]
hcp_map = {"Bennie": 36, "Adriaan": 33, "Danie": 33, "Martin": 32, "Frederik": 32}
course_par = [4, 4, 5, 3, 5, 4, 4, 3, 4, 4, 4, 5, 3, 5, 4, 4, 3, 4]
course_idx = [17, 3, 7, 5, 9, 13, 1, 15, 11, 14, 6, 8, 18, 10, 2, 4, 16, 12]

# Try to load existing data, otherwise create new table
try:
    df = load_data()
except:
    # Create empty tournament structure
    rows = []
    for p in players:
        for h in range(1, 19):
            rows.append({
                "Player": p, "Hole": h, "Score": 0, "Drinks": 0, 
                "Camo": False, "Throw": False, "Kick": False, "Mully": 0
            })
    df = pd.DataFrame(rows)
    save_data(df)

# --- CALCULATION LOGIC ---
def get_points(row):
    if row['Score'] == 0: return 0
    h_idx = int(row['Hole']) - 1
    hcp = hcp_map[row['Player']]
    par = course_par[h_idx]
    idx = course_idx[h_idx]
    strokes = (hcp // 18) + (1 if idx <= (hcp % 18) else 0)
    net = row['Score'] - strokes
    diff = net - par
    pts = 0
    if diff >= 2: pts = 0
    elif diff == 1: pts = 1
    elif diff == 0: pts = 2
    elif diff == -1: pts = 3
    elif diff == -2: pts = 4
    else: pts = 5
    return pts * 2 if row['Camo'] else pts

# --- HEADER ---
col_l, col_mid, col_r = st.columns([1, 2, 1])
with col_mid:
    try: st.image("Naboom logo Nuut.png", use_container_width=True)
    except: st.markdown("<h1 style='text-align: center;'>🚀</h1>", unsafe_allow_html=True)
st.markdown("<h1 class='neon-text'>NABOOM NUUT: TACTICAL OPEN</h1>", unsafe_allow_html=True)

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["🏆 LIVE LEADERBOARD", "🎒 THE ARSENAL", "🎯 SCORE INPUT"])

with tab1:
    df['Points'] = df.apply(get_points, axis=1)
    summary = df.groupby("Player").agg({
        'Points': 'sum', 'Score': 'sum', 'Drinks': 'sum'
    }).reset_index()
    summary['Gimme (cm)'] = summary['Drinks'] * 10
    st.table(summary.sort_values("Points", ascending=False))
    if st.button("🔄 Sync Scores"): st.rerun()

with tab2:
    for p in players:
        p_df = df[df['Player'] == p]
        with st.expander(f"📊 {p}'s Equipment"):
            c1, c2, c3, c4 = st.columns(4)
            camo_h = p_df[p_df['Camo'] == True]['Hole'].values
            c1.metric("Camo Ball", f"Hole {camo_h[0]}" if len(camo_h)>0 else "READY")
            c2.metric("Mulligans", 2 - p_df['Mully'].sum())
            c3.metric("Gimme", f"{p_df['Drinks'].sum()*10}cm")
            # Resource counting for Throws/Kicks
            curr_hole = st.session_state.get('active_hole', 1)
            half_range = range(1,10) if curr_hole <= 9 else range(10,19)
            t_used = p_df[p_df['Hole'].isin(half_range)]['Throw'].any()
            k_used = p_df[p_df['Hole'].isin(half_range)]['Kick'].any()
            c4.write(f"**Throw:** {'❌' if t_used else '✅'} | **Kick:** {'❌' if k_used else '✅'}")

with tab3:
    hole = st.number_input("Select Hole", 1, 18, key='active_hole')
    st.markdown(f"### ⛳ Hole {hole} (Par {course_par[hole-1]})")
    
    for p in players:
        idx = df[(df['Player'] == p) & (df['Hole'] == hole)].index[0]
        with st.container():
            c1, c2, c3, c4, c5, c6 = st.columns([1,1,1,1,1,1])
            df.at[idx, 'Score'] = c1.number_input(f"Score ({p})", 0, 15, value=int(df.at[idx, 'Score']), key=f"s{p}{hole}")
            df.at[idx, 'Drinks'] = c2.number_input(f"Drinks ({p})", 0, 10, value=int(df.at[idx, 'Drinks']), key=f"d{p}{hole}")
            
            # Action Buttons (Toggle logic)
            if c3.checkbox("Camo", value=bool(df.at[idx, 'Camo']), key=f"c{p}{hole}"): df.at[idx, 'Camo'] = True
            if c4.checkbox("Throw", value=bool(df.at[idx, 'Throw']), key=f"t{p}{hole}"): df.at[idx, 'Throw'] = True
            if c5.checkbox("Kick", value=bool(df.at[idx, 'Kick']), key=f"k{p}{hole}"): df.at[idx, 'Kick'] = True
            if c6.button("Mully", key=f"m{p}{hole}"): df.at[idx, 'Mully'] = 1
        st.divider()
    
    if st.button("💾 SAVE & SYNC ALL PHONES", use_container_width=True):
        save_data(df)
        st.success("Scores Uploaded to Cloud!")
