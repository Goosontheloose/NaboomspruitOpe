import streamlit as st
import pandas as pd

# --- APP CONFIG & STYLING ---
st.set_page_config(page_title="Neon Fairway Open", layout="wide")

# Custom CSS for Cyber-Turf Aesthetic
st.markdown("""
    <style>
    .stApp {
        background-color: #050505;
        color: #FFFFFF;
    }
    .main-header {
        font-family: 'Lexend', sans-serif;
        font-weight: 800;
        font-size: 3rem;
        color: #BFFF00;
        text-shadow: 0 0 20px #BFFF00;
        text-align: center;
        padding: 20px;
    }
    .player-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(0, 240, 255, 0.3);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 10px;
        backdrop-filter: blur(12px);
    }
    .stat-label {
        font-family: 'IBM Plex Mono', monospace;
        color: #00F0FF;
        font-size: 0.8rem;
    }
    .powerup-active { color: #BFFF00; font-weight: bold; }
    .powerup-spent { color: #FF0090; text-decoration: line-through; opacity: 0.5; }
    </style>
    """, unsafe_allow_html=True)

# --- COURSE DATA ---
COURSE_DATA = {
    'Hole': list(range(1, 19)),
    'Par': [4, 4, 5, 3, 5, 4, 4, 3, 4, 4, 4, 5, 3, 5, 4, 4, 3, 4],
    'Stroke': [17, 3, 7, 5, 9, 13, 1, 15, 11, 14, 6, 8, 18, 10, 2, 4, 16, 12]
}
players = ["Adriaan", "Danie", "Frederik", "Bennie", "Martin"]

# --- STATE MANAGEMENT ---
if 'scores' not in st.session_state:
    st.session_state.scores = {p: [0]*18 for p in players}
if 'powerups' not in st.session_state:
    st.session_state.powerups = {p: {
        'Camo': [False]*18,
        'Me2': False,
        'Throws': [0, 0], # [Front 9 used, Back 9 used]
        'Kicks': [0, 0],  # [Front 9 used, Back 9 used]
        'Mulligans': 0    # Total used (max 2)
    } for p in players}
if 'current_hole' not in st.session_state:
    st.session_state.current_hole = 1

# --- LOGIC HELPERS ---
def calculate_total(player):
    total = 0
    for h in range(18):
        s = st.session_state.scores[player][h]
        if st.session_state.powerups[player]['Camo'][h]:
            total += (s * 2)
        else:
            total += s
    return total

# --- UI LAYOUT ---
st.markdown('<div class="main-header">NEON FAIRWAY OPEN</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🏆 LEADERBOARD", "🎯 HOLE COMMAND"])

with tab1:
    st.subheader("Tournament Rankings")
    leaderboard_data = []
    for p in players:
        total = calculate_total(p)
        par_diff = total - sum(COURSE_DATA['Par'][:st.session_state.current_hole]) if total > 0 else 0
        
        # Powerup Status Strings
        p_data = st.session_state.powerups[p]
        mull_status = f"{2 - p_data['Mulligans']} Left"
        throw_status = "Available" if (st.session_state.current_hole <= 9 and p_data['Throws'][0] == 0) or (st.session_state.current_hole > 9 and p_data['Throws'][1] == 0) else "Spent"
        
        leaderboard_data.append({
            "Player": p,
            "Total": total,
            "vs Par": f"{par_diff:+}" if par_diff != 0 else "E",
            "Mulligans": mull_status,
            "Throw/Kick": throw_status
        })
    
    df = pd.DataFrame(leaderboard_data).sort_values(by="Total")
    st.table(df)

with tab2:
    hole_idx = st.session_state.current_hole - 1
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"### HOLE {st.session_state.current_hole} (Par {COURSE_DATA['Par'][hole_idx]})")
        st.write(f"Difficulty Stroke: {COURSE_DATA['Stroke'][hole_idx]}")
        
        for p in players:
            with st.expander(f"{p}'s Score Card"):
                cols = st.columns(3)
                # Stroke Input
                st.session_state.scores[p][hole_idx] = cols[0].number_input(f"Strokes", min_value=0, max_value=20, key=f"score_{p}")
                
                # Camo Ball Toggle
                st.session_state.powerups[p]['Camo'][hole_idx] = cols[1].checkbox("Camo Ball (x2)", key=f"camo_{p}")
                
                # Limited Powerups
                p_p = st.session_state.powerups[p]
                half_idx = 0 if st.session_state.current_hole <= 9 else 1
                
                if cols[2].button(f"Use Throw/Kick", key=f"tk_{p}"):
                    if p_p['Throws'][half_idx] == 0:
                        p_p['Throws'][half_idx] = 1
                        st.success("Powerup Activated")
                    else:
                        st.error("Already used for this nine!")
                
                if cols[2].button(f"Use Mulligan", key=f"mul_{p}"):
                    if p_p['Mulligans'] < 2:
                        p_p['Mulligans'] += 1
                        st.success("Mulligan Logged")
                    else:
                        st.error("No Mulligans left!")

    if st.button("NEXT HOLE ➔", use_container_width=True):
        if st.session_state.current_hole < 18:
            st.session_state.current_hole += 1
            st.rerun()
