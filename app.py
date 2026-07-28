import streamlit as st
import pandas as pd
import gspread
import os
from google.oauth2.service_account import Credentials

# --- APP CONFIG ---
st.set_page_config(page_title="Naboom Nuut: Tactical Open", layout="wide")

# Initialize Reset Counter to force UI refresh
if 'reset_id' not in st.session_state:
    st.session_state.reset_id = 0

# --- UI STYLING ---
st.markdown("""
    <style>
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; margin-bottom: 20px; }
    .main-title { color: #BFFF00; font-size: 2.2rem; font-weight: 800; text-transform: uppercase; margin-top: 10px; letter-spacing: 2px; }
    
    /* Ranking Table Styling */
    .rank-table { width: 100%; border-collapse: collapse; margin-top: 20px; background-color: #0F0F0F; }
    .rank-table th { background-color: #1A1A1A; color: #BFFF00; padding: 15px; text-align: left; border-bottom: 2px solid #333; text-transform: uppercase; font-size: 0.9rem; }
    .rank-table td { padding: 15px; border-bottom: 1px solid #222; color: #EEE; font-size: 1.1rem; }
    .rank-1 { color: #FFD700; font-weight: bold; border-left: 5px solid #FFD700; }
    .pts-highlight { color: #BFFF00; font-weight: 800; font-size: 1.3rem; }
    .gimme-highlight { color: #00D1FF; font-family: monospace; }

    /* Scorecard Grid */
    .sc-table { width: 100%; border-collapse: collapse; background-color: #0F0F0F; color: #EEE; font-size: 0.75rem; table-layout: fixed; }
    .sc-table th, .sc-table td { border: 1px solid #333; padding: 8px 2px; text-align: center; vertical-align: middle; }
    .sc-table th { background-color: #1A1A1A; color: #BFFF00; font-size: 0.6rem; }
    
    .player-cell { text-align: left !important; font-weight: bold; background: #151515; padding-left: 8px !important; width: 95px !important; color: #FFF; border-left: 4px solid #BFFF00 !important; }
    .score-val { font-size: 0.9rem; font-weight: 700; color: #FFF; }
    .pts-val { font-size: 0.85rem; font-weight: 800; color: #BFFF00; }
    .divider { color: #555; margin: 0 3px; }
    
    .tag-container { display: flex; flex-wrap: wrap; justify-content: center; gap: 3px; margin-top: 5px; min-height: 12px; }
    .p-tag { font-size: 0.55rem; font-weight: 900; padding: 2px 3px; border-radius: 2px; text-transform: uppercase; line-height: 1; }
    
    .t-tag { color: #FF8C00; border: 1px solid #FF8C00; } 
    .k-tag { color: #FF3E3E; border: 1px solid #FF3E3E; } 
    .m-tag { color: #BF00FF; border: 1px solid #BF00FF; } 
    .me-tag { color: #00D1FF; border: 1px solid #00D1FF; background: rgba(0, 209, 255, 0.2); }
    .ld-tag { color: #00FFCC; border: 1px solid #00FFCC; background: rgba(0, 255, 204, 0.2); }
    .cp-tag { color: #FFCC00; border: 1px solid #FFCC00; background: rgba(255, 204, 0, 0.2); }
    
    .camo-active { background-color: #1E2B00 !important; border: 1px solid #BFFF00 !important; }
    .total-box { background: #1A1A1A; font-weight: bold; font-size: 0.9rem; }
    </style>
    """, unsafe_allow_html=True)

# --- CONSTANTS ---
LOCAL_LOGO = "Naboom logo Nuut.png"
PLAYERS = ["Bennie", "Adriaan", "Danie", "Martin", "Frederik"]
HCP_MAP = {"BENNIE": 36, "ADRIAAN": 33, "DANIE": 33, "MARTIN": 32, "FREDERIK": 32}
COURSE_PAR = [4, 4, 5, 3, 5, 4, 4, 3, 4, 4, 4, 5, 3, 5, 4, 4, 3, 4]
COURSE_IDX = [17, 3, 7, 5, 9, 13, 1, 15, 11, 14, 6, 8, 18, 10, 2, 4, 16, 12]

# --- DATA ENGINE ---
def get_database():
    try:
        s = st.secrets["connections"]["gsheets"]
        creds = Credentials.from_service_account_info(s, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        ws = client.open_by_key(s["spreadsheet"].strip()).get_worksheet(0)
        data = ws.get_all_values()
        if len(data) < 2: return pd.DataFrame(), ws
        df_cloud = pd.DataFrame(data[1:], columns=['player', 'hole', 'score', 'drinks', 'camo', 'throw', 'kick', 'mully', 'me2', 'honor'])
        return df_cloud, ws
    except: return pd.DataFrame(), None

def get_master_df(df_cloud):
    rows = []
    for h in range(1, 19):
        for p in PLAYERS:
            rows.append({"player": p.upper(), "hole": str(h), "score": 0, "drinks": 0, "camo": "FALSE", "throw": "FALSE", "kick": "FALSE", "mully": 0, "me2": "FALSE", "honor": "NONE"})
    master = pd.DataFrame(rows)
    
    if not df_cloud.empty:
        df_cloud['player'] = df_cloud['player'].astype(str).str.strip().str.upper()
        df_cloud['hole'] = df_cloud['hole'].astype(str).str.strip()
        master = master.merge(df_cloud, on=['player', 'hole'], how='left', suffixes=('', '_c'))
        cols = ['score', 'drinks', 'camo', 'throw', 'kick', 'mully', 'me2', 'honor']
        for col in cols:
            if f"{col}_c" in master.columns:
                master[col] = master[f"{col}_c"].combine_first(master[col])
        master = master[["player", "hole"] + cols]

    master['score'] = pd.to_numeric(master['score'], errors='coerce').fillna(0).astype(int)
    master['drinks'] = pd.to_numeric(master['drinks'], errors='coerce').fillna(0).astype(int)
    master['hole'] = pd.to_numeric(master['hole']).astype(int)
    master['mully'] = pd.to_numeric(master['mully'], errors='coerce').fillna(0).astype(int)
    master['player_disp'] = master['player'].map({p.upper(): p for p in PLAYERS})
    return master

def calculate_points(p_name, h_num, score, camo):
    if score <= 0: return 0
    h_idx = int(h_num) - 1
    par = COURSE_PAR[h_idx]
    hcp = HCP_MAP.get(str(p_name).upper(), 0)
    strokes = (hcp // 18) + (1 if COURSE_IDX[h_idx] <= (hcp % 18) else 0)
    net = score - strokes
    pts = max(0, 2 - (net - par))
    if pts > 0 and par in [3, 5]: pts += 1 
    return pts * 2 if str(camo).upper() == "TRUE" else pts

# --- HEADER LOGIC ---
st.markdown('<div class="header-container">', unsafe_allow_html=True)
if os.path.exists(LOCAL_LOGO):
    st.image(LOCAL_LOGO, width=150)
st.markdown('<div class="main-title">Naboom Nuut: Tactical Open</div></div>', unsafe_allow_html=True)

# --- APP FLOW ---
df_raw, worksheet = get_database()
df = get_master_df(df_raw)
df['pts'] = df.apply(lambda r: calculate_points(r['player'], r['hole'], r['score'], r['camo']), axis=1)

tab0, tab1, tab2, tab3 = st.tabs(["🥇 RANKINGS", "🏆 LIVE SCORECARD", "🎒 THE ARSENAL", "🎯 HOLE COMMAND"])

with tab0:
    st.subheader("Tournament Leaderboard")
    rank_data = []
    for p in PLAYERS:
        p_df = df[df['player_disp'] == p]
        total_pts = p_df['pts'].sum()
        total_drinks = p_df['drinks'].sum()
        rank_data.append({"Player": p, "Points": total_pts, "Gimme": total_drinks * 10})
    
    leaderboard = pd.DataFrame(rank_data).sort_values(by="Points", ascending=False).reset_index(drop=True)
    leaderboard.index += 1
    
    rank_html = '<table class="rank-table"><tr><th>Rank</th><th>Player</th><th>Total Points</th><th>Gimme Distance</th></tr>'
    for i, row in leaderboard.iterrows():
        r_class = "rank-1" if i == 1 else ""
        rank_html += f"""<tr class="{r_class}"><td>{i}</td><td style="font-weight:bold;">{row['Player']}</td><td class="pts-highlight">{int(row['Points'])}</td><td class="gimme-highlight">📏 {int(row['Gimme'])} cm</td></tr>"""
    st.markdown(rank_html + "</table>", unsafe_allow_html=True)

with tab1:
    html = '<table class="sc-table"><tr><th style="width:95px">PLAYER</th>'
    for h in range(1, 19): html += f'<th>H{h}<br><span style="color:#666">P{COURSE_PAR[h-1]}</span></th>'
    html += '<th class="total-box">TOT</th><th class="total-box" style="color:#BFFF00">PTS</th></tr>'
    for p in PLAYERS:
        p_df = df[df['player_disp'] == p].sort_values('hole')
        html += f'<tr><td class="player-cell">{p}</td>'
        for _, r in p_df.iterrows():
            is_camo = str(r['camo']).upper() == "TRUE"
            tags = []
            if str(r['throw']).upper() == "TRUE": tags.append('<span class="p-tag t-tag">T</span>')
            if str(r['kick']).upper() == "TRUE": tags.append('<span class="p-tag k-tag">K</span>')
            if int(r['mully']) > 0: tags.append('<span class="p-tag m-tag">M</span>')
            if str(r['me2']).upper() == "TRUE": tags.append('<span class="p-tag me-tag">ME</span>')
            if str(r['honor']).upper() == "D": tags.append('<span class="p-tag ld-tag">LD</span>')
            if str(r['honor']).upper() == "C": tags.append('<span class="p-tag cp-tag">CP</span>')
            tag_html = f'<div class="tag-container">{"".join(tags)}</div>' if tags else ""
            s_val = int(r['score']) if r['score'] > 0 else "-"
            p_val = int(r['pts']) if r['score'] > 0 else "-"
            html += f'<td class="{"camo-active" if is_camo else ""}"><span class="score-val">{s_val}</span><span class="divider">|</span><span class="pts-val">{p_val}</span>{tag_html}</td>'
        html += f'<td class="total-box">{int(p_df["score"].sum())}</td><td class="total-box" style="color:#BFFF00">{int(p_df["pts"].sum())}</td></tr>'
    st.markdown(html + "</table>", unsafe_allow_html=True)

with tab2:
    st.subheader("Tactical Resource Inventory")
    inv = []
    for p in PLAYERS:
        p_df = df[df['player_disp'] == p]
        inv.append({
            "Player": p, "Gimme Distance": f"📏 {int(p_df['drinks'].sum()) * 10} cm",
            "Camo Balls": f"Used {(p_df['camo'].astype(str).str.upper() == 'TRUE').sum()} / 2",
            "Me2": "✅ USED" if (p_df['me2'].astype(str).str.upper() == "TRUE").any() else "READY",
            "Mullies": f"{int(p_df['mully'].sum())} / 2",
            "Throws": (p_df['throw'].astype(str).str.upper() == "TRUE").sum(),
            "Kicks": (p_df['kick'].astype(str).str.upper() == "TRUE").sum()
        })
    st.table(inv)

with tab3:
    h_idx = st.selectbox("Select Hole", range(1, 19))
    par_val = COURSE_PAR[h_idx-1]
    if st.button("🚨 CLEAR EVERYTHING FOR THIS HOLE", use_container_width=True):
        if worksheet:
            reset_data = [[p, str(h_idx), "0", "0", "FALSE", "FALSE", "FALSE", "0", "FALSE", "NONE"] for p in PLAYERS]
            start_row = ((h_idx-1)*5)+2
            worksheet.update(range_name=f"A{start_row}:J{start_row+4}", values=reset_data)
            st.session_state.reset_id += 1
            st.rerun()

    h_data = df[df['hole'] == h_idx]
    with st.form(f"entry_form_v{st.session_state.reset_id}"):
        st.info(f"Hole {h_idx} | Par {par_val}")
        updates = []
        for p in PLAYERS:
            try: p_row = h_data[h_data['player'] == p.upper()].iloc[0]
            except: p_row = {"score":0, "drinks":0, "camo":"FALSE", "throw":"FALSE", "kick":"FALSE", "mully":0, "me2":"FALSE", "honor":"NONE"}
            st.markdown(f"**{p}**")
            c = st.columns([1, 1, 1, 1, 1, 1, 1, 1.2]); rid = st.session_state.reset_id
            s = c[0].number_input("Score", 0, 15, int(p_row['score']), key=f"s_{p}_{rid}")
            d = c[1].number_input("Drink", 0, 10, int(p_row['drinks']), key=f"d_{p}_{rid}")
            ca = c[2].checkbox("Camo", str(p_row['camo']).upper() == "TRUE", key=f"ca_{p}_{rid}")
            th = c[3].checkbox("Thr", str(p_row['throw']).upper() == "TRUE", key=f"th_{p}_{rid}")
            ki = c[4].checkbox("Kck", str(p_row['kick']).upper() == "TRUE", key=f"ki_{p}_{rid}")
            mu = c[5].number_input("Mly", 0, 1, int(p_row['mully']), key=f"mu_{p}_{rid}")
            me = c[6].checkbox("Me2", str(p_row['me2']).upper() == "TRUE", key=f"me_{p}_{rid}")
            h_val = "NONE"
            if par_val == 5:
                if c[7].checkbox("Drive (LD)", str(p_row['honor']).upper() == "D", key=f"hd_{p}_{rid}"): h_val = "D"
            elif par_val == 3:
                if c[7].checkbox("Pin (CP)", str(p_row['honor']).upper() == "C", key=f"hc_{p}_{rid}"): h_val = "C"
            updates.append([p, str(h_idx), str(s), str(d), str(ca).upper(), str(th).upper(), str(ki).upper(), str(mu), str(me).upper(), h_val])
        if st.form_submit_button(f"SAVE HOLE {h_idx}"):
            if worksheet:
                start_row = ((h_idx-1)*5)+2
                worksheet.update(range_name=f"A{start_row}:J{start_row+4}", values=updates)
                st.success("Synced!"); st.rerun()
