import streamlit as st
import pandas as pd

# --- APP CONFIG & STYLING ---
st.set_page_config(page_title="Naboom Nuut: Tactical Open", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #FFFFFF; }
    .neon-text { color: #BFFF00; text-shadow: 0 0 10px #BFFF00; }
    .stats-box { border: 1px solid #BFFF00; padding: 10px; border-radius: 5px; background: rgba(191, 255, 0, 0.05); }
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
        'Camo': [False]*18, 'Me2': False, 
        'Throws': [0, 0], 'Kicks': [0, 0], # Index 0 = Front 9, Index 1 = Back 9
        'Mulligans': 0
    } for p in players}
if 'current_hole' not in st.session_state:
    st.session_state.current_hole = 1

# --- CALCULATION LOGIC ---
def get_net_score(player, hole_idx):
    gross = st.session_state.scores[player][hole_idx]
    if gross == 0: return 0
    hcp = HANDICAPS[player]
    strokes_received = (hcp // 18) + (1 if COURSE['Index'][hole_idx] <= (hcp % 18) else 0)
    net = gross - strokes_received
    if st.session_state.powerups[player]['Camo'][hole_idx]: net *= 2
    return net

# --- HEADER ---
col1, col2 = st.columns([1, 4])
with col1:
    try: st.image("Naboom logo Nuut.png", width=120)
    except: st.markdown("🚀")
with col2:
    st.markdown("<h1 class='neon-text'>NABOOM NUUT: TACTICAL OPEN</h1>", unsafe_allow_html=True)

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["🏆 LEADERBOARD", "🎒 THE ARSENAL", "🎯 HOLE COMMAND"])

with tab1:
    lb_data = []
    for p in players:
        net_total = sum([get_net_score(p, i) for i in range(18)])
        lb_data.append({
            "Player": p,
            "Gross": sum(st.session_state.scores[p]),
            "Net": net_total,
            "Total Drinks": sum(st.session_state.drinks[p]),
            "Gimme (cm)": sum(st.session_state.drinks[p]) * 10
        })
    st.table(pd.DataFrame(lb_data).sort_values("Net"))

with tab2:
    st.subheader("Tactical Resource Inventory")
    half = 0 if st.session_state.current_hole <= 9 else 1
    
    for p in players:
        with st.expander(f"📊 {p}'s Equipment Check"):
            p_pwr = st.session_state.powerups[p]
            c1, c2, c3, c4 = st.columns(4)
            
            # Separate Kick and Throw
            t_status = "✅ READY" if p_pwr['Throws'][half] == 0 else "❌ USED"
            k_status = "✅ READY" if p_pwr['Kicks'][half] == 0 else "❌ USED"
            
            c1.metric("Mulligans", 2 - p_pwr['Mulligans'])
            c2.write(f"**Throw:** {t_status}")
            c3.write(f"**Kick:** {k_status}")
            
            # Gimme Distance Calculation
            total_drinks = sum(st.session_state.drinks[p])
            gimme_cm = total_drinks * 10
            c4.metric("Gimme Gauge", f"{gimme_cm}cm", f"{total_drinks} drinks")

with tab3:
    h_idx = st.session_state.current_hole - 1
    st.markdown(f"### ⛳ HOLE {st.session_state.current_hole} (Par {COURSE['Par'][h_idx]})")
    
    for p in players:
        with st.container():
            st.write(f"**{p}**")
            c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1])
            
            st.session_state.scores[p][h_idx] = c1.number_input("Strokes", 0, 15, key=f"s_{p}")
            st.session_state.drinks[p][h_idx] = c2.number_input("Drinks", 0, 10, key=f"d_{p}")
            st.session_state.powerups[p]['Camo'][h_idx] = c3.checkbox("Camo", key=f"c_{p}")
            
            if c4.button("Throw", key=f"t_{p}"):
                st.session_state.powerups[p]['Throws'][half] = 1
                st.toast(f"{p} used their Throw!")
                
            if c5.button("Kick", key=f"k_{p}"):
                st.session_state.powerups[p]['Kicks'][half] = 1
                st.toast(f"{p} used their Kick!")
        st.divider()

    if st.button("LOCK HOLE & ADVANCE", use_container_width=True):
        if st.session_state.current_hole < 18:
            st.session_state.current_hole += 1
            st.rerun()
