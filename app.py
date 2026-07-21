import streamlit as st
import pandas as pd

# --- APP CONFIG & STYLING ---
st.set_page_config(page_title="Naboomspruit Ope 2026", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #FFFFFF; }
    .neon-text { 
        color: #BFFF00; 
        text-shadow: 0 0 10px #BFFF00; 
        text-align: center; 
        width: 100%;
    }
    .inventory-card { 
        padding: 15px; 
        border-radius: 10px; 
        border: 1px solid #333; 
        background: rgba(255,255,255,0.03);
        margin-bottom: 10px;
    }
    /* Centering helper for images in columns */
    [data-testid="stHorizontalBlock"] {
        align-items: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- COURSE & PLAYER DATA ---
COURSE = {
    'Par': [4, 4, 5, 3, 5, 4, 4, 3, 4, 4, 4, 5, 3, 5, 4, 4, 3, 4],
    'Index': [17, 3, 7, 5, 9, 13, 1, 15, 11, 14, 6, 8, 18, 10, 2, 4, 16, 12]
}

HANDICAPS = {
    "Bennie": 36, "Adriaan": 33, "Danie": 33, "Martin": 32, "Frederik": 32
}
players = list(HANDICAPS.keys())

# --- SESSION STATE INITIALIZATION ---
if 'scores' not in st.session_state:
    st.session_state.scores = {p: [0]*18 for p in players}
if 'drinks' not in st.session_state:
    st.session_state.drinks = {p: [0]*18 for p in players}
if 'powerups' not in st.session_state:
    st.session_state.powerups = {p: {
        'CamoUsed': False, 'CamoHole': None,
        'Me2': False, 
        'Throws': [0, 0], 'Kicks': [0, 0], 
        'Mulligans': 0
    } for p in players}
if 'current_hole' not in st.session_state:
    st.session_state.current_hole = 1

# --- CALCULATION LOGIC ---
def get_net_score(player, hole_idx):
    gross = st.session_state.scores[player][hole_idx]
    if gross == 0: return 0
    hcp = HANDICAPS[player]
    received = (hcp // 18) + (1 if COURSE['Index'][hole_idx] <= (hcp % 18) else 0)
    net = gross - received
    if st.session_state.powerups[player]['CamoUsed'] and st.session_state.powerups[player]['CamoHole'] == hole_idx + 1:
        net *= 2
    return net

# --- HEADER (CENTERED) ---
# We create 3 columns and put the logo in the middle one (index 1)
col_l, col_mid, col_r = st.columns([1, 2, 1])

with col_mid:
    try: 
        # Display the logo in the center column
        st.image("Naboom logo Nuut.png", use_container_width=True)
    except: 
        st.markdown("<h1 style='text-align: center;'>🚀</h1>", unsafe_allow_html=True)

# Title is also centered via the CSS class 'neon-text'
st.markdown("<h1 class='neon-text'>NABOOMSPRUIT OPE : 2026</h1>", unsafe_allow_html=True)
st.divider()

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["🏆 LEADERBOARD", "🎒 THE ARSENAL", "🎯 HOLE COMMAND"])

with tab1:
    lb_data = []
    for p in players:
        net_total = sum([get_net_score(p, i) for i in range(18)])
        lb_data.append({
            "Player": p, "Gross": sum(st.session_state.scores[p]),
            "Net": net_total, "Drinks": sum(st.session_state.drinks[p]),
            "Gimme": f"{sum(st.session_state.drinks[p]) * 10}cm"
        })
    st.table(pd.DataFrame(lb_data).sort_values("Net"))

with tab2:
    st.subheader("Tactical Inventory Status")
    half = 0 if st.session_state.current_hole <= 9 else 1
    
    for p in players:
        p_pwr = st.session_state.powerups[p]
        with st.container():
            st.markdown(f"### {p}")
            c1, c2, c3, c4, c5 = st.columns(5)
            
            camo_status = f"🎯 HOLE {p_pwr['CamoHole']}" if p_pwr['CamoUsed'] else "✅ READY"
            c1.metric("Camo Ball", camo_status)
            
            t_status = "✅ READY" if p_pwr['Throws'][half] == 0 else "❌ USED"
            k_status = "✅ READY" if p_pwr['Kicks'][half] == 0 else "❌ USED"
            c2.write(f"**Throw:** {t_status}")
            c3.write(f"**Kick:** {k_status}")
            
            c4.metric("Mulligans", 2 - p_pwr['Mulligans'])
            c5.metric("Gimme Gauge", f"{sum(st.session_state.drinks[p]) * 10}cm")
            st.divider()

with tab3:
    h_idx = st.session_state.current_hole - 1
    st.markdown(f"### ⛳ HOLE {st.session_state.current_hole} (Par {COURSE['Par'][h_idx]})")
    
    for p in players:
        with st.container():
            c1, c2, c3, c4, c5, c6 = st.columns([1, 1, 1, 1, 1, 1])
            
            st.session_state.scores[p][h_idx] = c1.number_input(f"Score ({p})", 0, 15, key=f"s_{p}")
            st.session_state.drinks[p][h_idx] = c2.number_input(f"Drinks ({p})", 0, 10, key=f"d_{p}")
            
            if c3.button("Camo", key=f"cam_{p}", disabled=st.session_state.powerups[p]['CamoUsed']):
                st.session_state.powerups[p]['CamoUsed'] = True
                st.session_state.powerups[p]['CamoHole'] = st.session_state.current_hole
                st.toast(f"CAMO BALL DEPLOYED FOR {p}!")

            if c4.button("Throw", key=f"t_{p}", disabled=st.session_state.powerups[p]['Throws'][half] == 1):
                st.session_state.powerups[p]['Throws'][half] = 1
                st.toast(f"{p} used Throw!")

            if c5.button("Kick", key=f"k_{p}", disabled=st.session_state.powerups[p]['Kicks'][half] == 1):
                st.session_state.powerups[p]['Kicks'][half] = 1
                st.toast(f"{p} used Kick!")

            if c6.button("Mully", key=f"m_{p}", disabled=st.session_state.powerups[p]['Mulligans'] >= 2):
                st.session_state.powerups[p]['Mulligans'] += 1
                st.toast(f"Mulligan used by {p}!")
        st.divider()

    if st.button("LOCK HOLE & ADVANCE", use_container_width=True):
        if st.session_state.current_hole < 18:
            st.session_state.current_hole += 1
            st.rerun()
