import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- APP CONFIG ---
st.set_page_config(page_title="Naboom Nuut: Tactical Open", layout="wide")

# --- UI BRANDING & CENTERING ---
st.markdown("""
    <style>
    /* Center the header elements */
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; margin-bottom: 30px; }
    .main-title { color: #BFFF00; font-size: 2.5rem; font-weight: 800; text-transform: uppercase; margin-top: 15px; }
    
    /* Tactical Scorecard Styling */
    .sc-table { width: 100%; border-collapse: collapse; background-color: #0F0F0F; color: #EEE; font-size: 0.85rem; }
    .sc-table th, .sc-table td { border: 1px solid #2A2A2A; padding: 10px 4px; text-align: center; }
    .sc-table th { background-color: #1A1A1A; color: #BFFF00; }
    .player-cell { text-align: left !important; font-weight: bold; background: #151515; padding-left: 10px !important; }
    
    /* Powerup Visuals */
    .camo-active { background-color: #2D3D00 !important; border: 2px solid #BFFF00 !important; color: #BFFF00 !important; }
    .power-icon { font-size: 0.6rem; display: block; margin-top: 4px; font-weight: bold; opacity: 0.9; }
    .t-tag { color: #FF8C00; } .k-tag { color: #FF3E3E; } .m-tag { color: #BF00FF; }
    </style>
    """, unsafe_allow_html=True)

# --- CONSTANTS ---
LOGO_URL = "https://d2yln88910ulu4.cloudfront.net/chatFiles/2556e3b2-fcdd-43ee-8daa-629d4551df6e.png"
PLAYERS = ["Bennie", "Adriaan", "Danie", "Martin", "Frederik"]
HCP_MAP = {"Bennie": 36, "Adriaan": 33, "Danie": 33, "Martin": 32, "Frederik": 32}
COURSE_PAR = [4, 4, 5, 3, 5, 4, 4, 3, 4, 4, 4, 5, 3, 5, 4, 4, 3, 4]
COURSE_IDX = [17, 3, 7, 5, 9, 13, 1, 15, 11, 14, 6, 8, 18, 10, 2, 4, 16, 12]

# --- DATA ENGINE ---
def get_database():
    try:
        s = st.secrets["connections"]["gsheets"]
        creds = Credentials.from_service_account_info(s, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        ws = client.open_by_key(s["spreadsheet"].strip()).get_worksheet(0)
        
        raw = ws.get_all_records()
        df_cloud = pd.DataFrame(raw)
        
        # Standardize columns to lowercase for logic
        df_cloud.columns = [c.lower().strip() for c in df_cloud.columns]
        return df_cloud, ws
    except Exception as e:
        st.error(f"Connection Failed: {e}")
        return pd.DataFrame(), None

def get_master_df(df_cloud):
    # Create the skeleton for 5 players x 18 holes
    rows = []
    for h in range(1, 19):
        for p in PLAYERS:
            rows.append({"player": p, "hole": h, "score": 0, "drinks": 0, "camo": "FALSE", "throw": "FALSE", "kick": "FALSE", "mully": 0})
    master = pd.DataFrame(rows)
    
    if not df_cloud.empty:
        # Merge cloud data into our master skeleton
        master = master.merge(df_cloud, on=['player', 'hole'], how='left', suffixes=('', '_c'))
        # Prioritize cloud data over defaults
        for col in ['score', 'drinks', 'camo', 'throw', 'kick', 'mully']:
            if f"{col}_c" in master.columns:
                master[col] = master[f"{col}_c"].combine_first(master[col])
        master = master[list(rows[0].keys())] # Keep clean columns
    return master

def get_points(p, h, score, camo):
    if not score or int(score) == 0: return 0
    h_idx = int(h) - 1
    hcp = HCP_MAP.get(p, 0)
    strokes = (hcp // 18) + (1 if COURSE_IDX[h_idx] <= (hcp % 18) else 0)
    net = int(score) - strokes
    pts = max(0, 2 - (net - COURSE_PAR[h_idx]))
    return pts * 2 if str(camo).upper() == "TRUE" else pts

# --- HEADER ---
st.markdown(f"""
    <div class="header-container">
        <img src="{LOGO_URL}" width="120">
        <div class="main-title">Naboom Nuut: Tactical Open</div>
    </div>
    """, unsafe_allow_html=True)

df_raw, worksheet = get_database()
df = get_master_df(df_raw)

# --- NAVIGATION ---
tab1, tab2, tab3 = st.tabs(["🏆 LIVE SCORECARD", "🎒 THE ARSENAL", "🎯 HOLE COMMAND"])

with tab1:
    # Calculate Live Points
    df['pts'] = df.apply(lambda r: get_points(r['player'], r['hole'], r['score'], r['camo']), axis=1)
    
    html = '<table class="sc-table"><tr><th>PLAYER</th>'
    for h in range(1, 19): html += f'<th>{h}</th>'
    html += '<th>TOT</th><th>PTS</th></tr>'
    
    for p in PLAYERS:
        p_df = df[df['player'] == p].sort_values('hole')
        html += f'<tr><td class="player-cell">{p}</td>'
        
        for _, r in p_df.iterrows():
            is_camo = str(r['camo']).upper() == "TRUE"
            cls = "camo-active" if is_camo else ""
            
            tags = ""
            if str(r['throw']).upper() == "TRUE": tags += '<span class="power-icon t-tag">THROW</span>'
            if str(r['kick']).upper() == "TRUE": tags += '<span class="power-icon k-tag">KICK</span>'
            if int(r['mully'] or 0) > 0: tags += f'<span class="power-icon m-tag">MULLY x{int(r["mully"])}</span>'
            
            score_val = int(r['score']) if int(r['score']) > 0 else "-"
            html += f'<td class="{cls}">{score_val}{tags}</td>'
        
        html += f'<td style="background:#1A1A1A">{int(p_df["score"].sum())}</td>'
        html += f'<td style="background:#1A1A1A; color:#BFFF00; font-weight:bold;">{int(p_df["pts"].sum())}</td></tr>'
    
    st.markdown(html + '</table>', unsafe_allow_html=True)

with tab2:
    st.subheader("Tactical Resource Inventory")
    inv = []
    for p in PLAYERS:
        p_df = df[df['player'] == p]
        inv.append({
            "Player": p,
            "Camo Ball": "USED" if (p_df['camo'].astype(str).str.upper() == "TRUE").any() else "Ready",
            "Mullies Used": pd.to_numeric(p_df['mully']).sum(),
            "Total Throws/Kicks": (p_df['throw'].astype(str).str.upper() == "TRUE").sum() + (p_df['kick'].astype(str).str.upper() == "TRUE").sum()
        })
    st.table(inv)

with tab3:
    h_idx = st.selectbox("Select Hole", range(1, 19))
    h_data = df[df['hole'] == h_idx]
    
    with st.form("hole_entry"):
        st.write(f"### Recording Hole {h_idx}")
        updates = []
        for p in PLAYERS:
            p_row = h_data[h_data['player'] == p].iloc[0]
            
            # Show Strokes for the hole
            hcp = HCP_MAP[p]
            strokes = (hcp // 18) + (1 if COURSE_IDX[h_idx-1] <= (hcp % 18) else 0)
            st.markdown(f"**{p}** (Hole Strokes: {strokes})")
            
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            s = c1.number_input("Score", 0, 15, int(p_row['score']), key=f"s{p}")
            d = c2.number_input("Drinks", 0, 10, int(p_row['drinks']), key=f"d{p}")
            ca = c3.checkbox("Camo", str(p_row['camo']).upper() == "TRUE", key=f"ca{p}")
            th = c4.checkbox("Throw", str(p_row['throw']).upper() == "TRUE", key=f"th{p}")
            ki = c5.checkbox("Kick", str(p_row['kick']).upper() == "TRUE", key=f"ki{p}")
            mu = c6.number_input("Mully", 0, 2, int(p_row['mully']), key=f"mu{p}")
            updates.append([str(s), str(d), str(ca).upper(), str(th).upper(), str(ki).upper(), str(mu)])
            
        if st.form_submit_button(f"SAVE HOLE {h_idx}"):
            if worksheet:
                start_row = ((h_idx - 1) * 5) + 2
                worksheet.update(range_name=f"C{start_row}:H{start_row+4}", values=updates)
                st.success("Synced to Cloud!"); st.rerun()
