import streamlit as st
import pandas as pd
import urllib.parse

# --- APP CONFIG & STYLING ---
st.set_page_config(page_title="Naboom Nuut: Tactical Open", layout="wide")

# Custom CSS for the "Cyber-Turf" Aesthetic
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #FFFFFF; }
    .leaderboard-val { font-family: 'IBM Plex Mono'; color: #00F0FF; font-size: 1.2rem; font-weight: bold; }
    .neon-text { color: #BFFF00; text-shadow: 0 0 10px #BFFF00; }
    .stTable { background-color: rgba(255, 255, 255, 0.05); border-radius: 10px; }
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
if 'powerups' not in st.session_state:
    st.session_state.powerups = {p: {
        'Camo': [False]*18, 'Me2': False, 'Throws': [0, 0], 'Kicks': [0, 0], 'Mulligans': 0
    } for p in players}
if 'current_hole' not in st.session_state:
    st.session_state.current_hole = 1

# --- CALCULATION LOGIC ---
def get_net_score(player, hole_idx):
    gross = st.session_state.scores[player][hole_idx]
    if gross == 0: return 0
    
    hcp = HANDICAPS[player]
    strokes_received = hcp // 18
    if COURSE['Index'][hole_idx] <= (hcp % 18):
        strokes_received += 1
        
    net = gross - strokes_received
    if st.session_state.powerups[player]['Camo'][hole_idx]:
        net = net * 2
    return net

# --- HEADER & LOGO ---
# Fixed the syntax error here by removing the broken links
col1, col2 = st.columns([1, 4]) 

with col1:
    logo_filename = "Naboom logo Nuut.png"
    try:
        # This will load your logo from your GitHub folder
        st.image(logo_filename, width=150)
    except:
        st.markdown("🚀") # Shows if the image file isn't found yet

with col2:
    st.markdown("<h1 class='neon-text'>NABOOM NUUT: TACTICAL OPEN</h1>", unsafe_allow_html=True)

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["🏆 LEADERBOARD", "🎒 THE ARSENAL", "🎯 HOLE COMMAND"])

with tab1:
    lb_list = []
    for p in players:
        gross_total = sum(st.session_state.scores[p])
        net_total = sum([get_net_score(p, i) for i in range(18)])
        par_sum = sum(COURSE['Par'][:st.session_state.current_hole])
        par_diff = net_total - par_sum if net_total > 0 else 0
        
        lb_list.append({
            "Player": p,
            "Gross": gross_total,
            "Net": net_total,
            "vs Par": f"{par_diff:+}" if par_diff != 0 else "E"
        })
    st.table(pd.DataFrame(lb_list).sort_values("Net"))

with tab2:
    st.subheader("Remaining Powerups")
    for p in players:
        p_data = st.session_state.powerups[p]
        c1, c2, c3 = st.columns(3)
        c1.metric(p, f"Mulligans: {2 - p_data['Mulligans']}")
        half = 0 if st.session_state.current_hole <= 9 else 1
        tk_status = "READY" if p_data['Throws'][half] == 0 else "USED"
        c2.write(f"Throw/Kick: **{tk_status}**")
        c3.write(f"Me2: **{'READY' if not p_data['Me2'] else 'USED'}**")
        st.divider()

with tab3:
    h_idx = st.session_state.current_hole - 1
    st.markdown(f"### SCORING HOLE {st.session_state.current_hole} (Par {COURSE['Par'][h_idx]})")
    
    for p in players:
        with st.container():
            c1, c2, c3 = st.columns([2, 1, 1])
            st.session_state.scores[p][h_idx] = c1.number_input(f"{p} Strokes", 0, 20, key=f"s_{p}")
            st.session_state.powerups[p]['Camo'][h_idx] = c2.checkbox("Camo Ball", key=f"c_{p}")
            if c3.button("Use Throw/Kick", key=f"tk_b_{p}"):
                st.session_state.powerups[p]['Throws'][0 if st.session_state.current_hole <= 9 else 1] = 1
                st.toast(f"Powerup logged for {p}!")

    if st.button("LOCK HOLE & PROCEED ➔", use_container_width=True):
        if st.session_state.current_hole < 18:
            st.session_state.current_hole += 1
            st.rerun()
