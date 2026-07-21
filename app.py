import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os

# --- APP CONFIG ---
st.set_page_config(page_title="Naboom Nuut: Tactical Open", layout="wide")

# --- VISUAL STYLING (Centered Logo & Tactical Scorecard) ---
st.markdown("""
    <style>
    .centered-header { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; margin-bottom: 25px; }
    .main-title { color: #BFFF00; font-size: 2.2rem; font-weight: 800; letter-spacing: 2px; margin-top: 10px; }
    .stroke-badge { background-color: #222; color: #BFFF00; padding: 3px 12px; border-radius: 20px; font-size: 0.8rem; border: 1px solid #444; }
    
    /* Tactical Grid */
    .sc-table { width: 100%; border-collapse: collapse; background-color: #0F0F0F; color: #EEE; font-family: 'Courier New', monospace; font-size: 0.85rem; }
    .sc-table th, .sc-table td { border: 1px solid #2A2A2A; padding: 10px 5px; text-align: center; }
    .sc-table th { background-color: #1A1A1A; color: #BFFF00; font-weight: bold; }
    .player-name { text-align: left !important; font-weight: 900; background: #151515; padding-left: 10px !important; }
    
    /* Powerup Indicators */
    .camo-active { background-color: #2D3D00 !important; color: #BFFF00 !important; font-weight: bold; border: 1.5px solid #BFFF00 !important; }
    .power-tag { font-size: 0.6rem; display: block; margin-top: 3px; font-weight: bold; }
    .t-tag { color: #FF8C00; } .k-tag { color: #FF3E3E; } .m-tag { color: #BF00FF; }
    </style>
    """, unsafe_allow_html=True)

# --- SETTINGS & MAPS ---
players = ["Bennie", "Adriaan", "Danie", "Martin", "Frederik"]
hcp_map = {"Bennie": 36, "Adriaan": 33, "Danie": 33, "Martin": 32, "Frederik": 32}
course_par = [4, 4, 5, 3, 5, 4, 4, 3, 4, 4, 4, 5, 3, 5, 4, 4, 3, 4]
course_idx = [17, 3, 7, 5, 9, 13, 1, 15, 11, 14, 6, 8, 18, 10, 2, 4, 16, 12]

# --- ROBUST DATA ENGINE ---
def get_data():
    try:
        s = st.secrets["connections"]["gsheets"]
        creds = Credentials.from_service_account_info(s, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        ws = client.open_by_key(s["spreadsheet"].strip()).get_worksheet(0)
        
        # Robust loading: Clean headers of spaces and case sensitivity automatically
        raw_rows = ws.get_all_values()
        if not raw_rows: return pd.DataFrame()
        
        headers = [h.strip().lower() for h in raw_rows[0]]
        df = pd.DataFrame(raw_rows[1:], columns=headers)
        return df, ws
    except Exception as e:
        st.error(f"Sync Failed: {e}")
        return pd.DataFrame(), None

def save_hole(ws, hole_num, updates):
    # Calculate exact row start: 1 (header) + (Hole-1)*5 + 1
    start_row = ((hole_num - 1) * len(players)) + 2
    vals = []
    for p in players:
        d = updates[p]
        vals.append([d['score'], d['drinks'], str(d['camo']).upper(), str(d['throw']).upper(), str(d['kick']).upper(), d['mully']])
    # Update range C:H (Score, Drinks, Camo, Throw, Kick, Mully)
    ws.update(range_name=f"C{start_row}:H{start_row+4}", values=vals)

def get_points(player, hole, score, camo):
    if not score or int(score) == 0: return 0
    h_idx = int(hole) - 1
    hcp = hcp_map.get(player, 0)
    strokes = (hcp // 18) + (1 if course_idx[h_idx] <= (hcp % 18) else 0)
    net = int(score) - strokes
    pts = max(0, 2 - (net - course_par[h_idx]))
    return pts * 2 if str(camo).upper() == "TRUE" else pts

# --- UI HEADER ---
st.markdown('<div class="centered-header">', unsafe_allow_html=True)
if os.path.exists("Naboom logo Nuut.png"): st.image("Naboom logo Nuut.png", width=120)
st.markdown('<div class="main-title">NABOOM NUUT: TACTICAL OPEN</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

df, worksheet = get_data()

if not df.empty and worksheet:
    t1, t2, t3 = st.tabs(["🏆 LEADERBOARD", "🎒 ARSENAL", "🎯 COMMAND"])

    with t1:
        # Build Tactical HTML Grid
        html = '<table class="sc-table"><tr><th>PLAYER</th>'
        for h in range(1, 19): html += f'<th>{h}</th>'
        html += '<th>TOT</th><th>PTS</th></tr>'
        
        for p in players:
            p_df = df[df['player'].str.strip() == p].copy()
            p_df['pts'] = p_df.apply(lambda r: get_points(p, r['hole'], r['score'], r['camo']), axis=1)
            
            html += f'<tr><td class="player-name">{p}</td>'
            for _, r in p_df.sort_values('hole', key=lambda x: x.astype(int)).iterrows():
                is_camo = str(r['camo']).upper() == "TRUE"
                cls = "camo-active" if is_camo else ""
                
                tags = ""
                if str(r['throw']).upper() == "TRUE": tags += '<span class="power-tag t-tag">THROW</span>'
                if str(r['kick']).upper() == "TRUE": tags += '<span class="power-tag k-tag">KICK</span>'
                if int(r['mully'] or 0) > 0: tags += f'<span class="power-tag m-tag">MULLY x{r["mully"]}</span>'
                
                val = r['score'] if int(r['score'] or 0) > 0 else "-"
                html += f'<td class="{cls}">{val}{tags}</td>'
            
            total_s = pd.to_numeric(p_df['score']).sum()
            total_p = p_df['pts'].sum()
            html += f'<td style="background:#1A1A1A">{total_s}</td><td style="background:#1A1A1A; color:#BFFF00; font-weight:bold;">{total_p}</td></tr>'
        
        html += '</table>'
        st.markdown(html, unsafe_allow_html=True)
        
        # Drinks / Gimme Section
        st.divider()
        dr_df = df.groupby('player')['drinks'].apply(lambda x: pd.to_numeric(x).sum()).reset_index()
        dr_df['Gimme (cm)'] = dr_df['drinks'] * 10
        st.dataframe(dr_df.sort_values('drinks', ascending=False), hide_index=True, use_container_width=True)

    with t2:
        # Resource Inventory
        st.subheader("Tactical Resource Status")
        inv = []
        for p in players:
            p_df = df[df['player'].str.strip() == p]
            inv.append({
                "Player": p,
                "Camo Ball": "✅ USED" if (p_df['camo'].str.upper() == "TRUE").any() else "Ready",
                "9-Hole Throws/Kicks": (p_df['throw'].str.upper() == "TRUE").sum() + (p_df['kick'].str.upper() == "TRUE").sum(),
                "Total Mullies": pd.to_numeric(p_df['mully']).sum()
            })
        st.table(inv)

    with t3:
        # Score Entry
        h_idx = st.selectbox("Select Hole", range(1, 19))
        h_data = df[df['hole'].astype(int) == h_idx]
        
        with st.form("entry_form"):
            updates = {}
            for p in players:
                p_row = h_data[h_data['player'].str.strip() == p].iloc[0]
                
                # Dynamic Stroke Badge
                hcp = hcp_map[p]
                strokes = (hcp // 18) + (1 if course_idx[h_idx-1] <= (hcp % 18) else 0)
                st.markdown(f"**{p}** <span class='stroke-badge'>Allotted Strokes: {strokes}</span>", unsafe_allow_html=True)
                
                c1, c2, c3, c4, c5, c6 = st.columns(6)
                s = c1.number_input("Score", 0, 15, int(p_row['score'] or 0), key=f"s{p}")
                d = c2.number_input("Drinks", 0, 10, int(p_row['drinks'] or 0), key=f"d{p}")
                c = c3.checkbox("Camo", str(p_row['camo']).upper() == "TRUE", key=f"c{p}")
                t = c4.checkbox("Throw", str(p_row['throw']).upper() == "TRUE", key=f"t{p}")
                k = c5.checkbox("Kick", str(p_row['kick']).upper() == "TRUE", key=f"k{p}")
                m = c6.number_input("Mully", 0, 2, int(p_row['mully'] or 0), key=f"m{p}")
                updates[p] = {'score': s, 'drinks': d, 'camo': c, 'throw': t, 'kick': k, 'mully': m}
            
            if st.form_submit_button(f"🚀 SYNC HOLE {h_idx}"):
                save_hole(worksheet, h_idx, updates)
                st.success("Cloud Synchronized.")
                st.rerun()
