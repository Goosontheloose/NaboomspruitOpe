import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- APP CONFIG ---
st.set_page_config(page_title="Naboom Nuut: Tactical Open", layout="wide")

# --- UI STYLING (Centered Header & Tactical Grid) ---
st.markdown("""
    <style>
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; margin-bottom: 30px; }
    .main-title { color: #BFFF00; font-size: 2.5rem; font-weight: 800; text-transform: uppercase; margin-top: 15px; }
    .sc-table { width: 100%; border-collapse: collapse; background-color: #0F0F0F; color: #EEE; font-size: 0.85rem; }
    .sc-table th, .sc-table td { border: 1px solid #2A2A2A; padding: 10px 4px; text-align: center; }
    .sc-table th { background-color: #1A1A1A; color: #BFFF00; }
    .player-cell { text-align: left !important; font-weight: bold; background: #151515; padding-left: 10px !important; }
    .camo-active { background-color: #2D3D00 !important; border: 2px solid #BFFF00 !important; color: #BFFF00 !important; }
    .power-icon { font-size: 0.6rem; display: block; margin-top: 4px; font-weight: bold; }
    .t-tag { color: #FF8C00; } .k-tag { color: #FF3E3E; } .m-tag { color: #BF00FF; }
    </style>
    """, unsafe_allow_html=True)

# --- CONSTANTS ---
LOGO_URL = "https://d2yln88910ulu4.cloudfront.net/chatFiles/c210e3f7-57b2-4ff7-833e-889a87dd3520.png"
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
        
        # Load all values and force column names
        data = ws.get_all_values()
        if len(data) < 2: return pd.DataFrame(), ws
        
        df_cloud = pd.DataFrame(data[1:], columns=[c.lower().strip() for c in data[0]])
        return df_cloud, ws
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return pd.DataFrame(), None

def get_master_df(df_cloud):
    # Create the 90-row skeleton
    rows = []
    for h in range(1, 19):
        for p in PLAYERS:
            rows.append({"player": p, "hole": h, "score": 0, "drinks": 0, "camo": "FALSE", "throw": "FALSE", "kick": "FALSE", "mully": 0})
    master = pd.DataFrame(rows)
    
    if not df_cloud.empty:
        # Standardize for matching
        master['hole'] = master['hole'].astype(str)
        master['player'] = master['player'].astype(str).str.strip().str.upper()
        
        df_cloud['hole'] = df_cloud['hole'].astype(str)
        df_cloud['player'] = df_cloud['player'].astype(str).str.strip().str.upper()
        
        # Merge cloud data into skeleton
        master = master.merge(df_cloud, on=['player', 'hole'], how='left', suffixes=('', '_c'))
        
        # Pull values from cloud columns
        for col in ['score', 'drinks', 'camo', 'throw', 'kick', 'mully']:
            c_name = f"{col}_c"
            if c_name in master.columns:
                master[col] = master[c_name].combine_first(master[col])
        
        master = master[["player", "hole", "score", "drinks", "camo", "throw", "kick", "mully"]]
    
    # Final type fix for math
    master['score'] = pd.to_numeric(master['score'], errors='coerce').fillna(0).astype(int)
    master['hole'] = pd.to_numeric(master['hole']).astype(int)
    # Restore original casing for display
    name_map = {p.upper(): p for p in PLAYERS}
    master['player'] = master['player'].map(name_map)
    return master

def get_points(p, h, score, camo):
    if score == 0: return 0
    h_idx = int(h) - 1
    hcp = HCP_MAP.get(p, 0)
    strokes = (hcp // 18) + (1 if COURSE_IDX[h_idx] <= (hcp % 18) else 0)
    net = score - strokes
    pts = max(0, 2 - (net - COURSE_PAR[h_idx]))
    return pts * 2 if str(camo).upper() == "TRUE" else pts

# --- HEADER ---
st.markdown(f'<div class="header-container"><img src="{LOGO_URL}" width="150"><div class="main-title">Naboom Nuut: Tactical Open</div></div>', unsafe_allow_html=True)

df_raw, worksheet = get_database()
df = get_master_df(df_raw)

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["🏆 LIVE SCORECARD", "🎒 THE ARSENAL", "🎯 HOLE COMMAND"])

with tab1:
    df['pts'] = df.apply(lambda r: get_points(r['player'], r['hole'], r['score'], r['camo']), axis=1)
    
    html = '<table class="sc-table"><tr><th>PLAYER</th>' + "".join([f'<th>{h}</th>' for h in range(1, 19)]) + '<th>TOT</th><th>PTS</th></tr>'
    for p in PLAYERS:
        p_df = df[df['player'] == p].sort_values('hole')
        html += f'<tr><td class="player-cell">{p}</td>'
        for _, r in p_df.iterrows():
            is_camo = str(r['camo']).upper() == "TRUE"
            tags = "".join([
                f'<span class="power-icon t-tag">THROW</span>' if str(r['throw']).upper() == "TRUE" else "",
                f'<span class="power-icon k-tag">KICK</span>' if str(r['kick']).upper() == "TRUE" else "",
                f'<span class="power-icon m-tag">MULLY x{int(float(r["mully"]))}</span>' if int(float(r['mully'] or 0)) > 0 else ""
            ])
            val = r['score'] if r['score'] > 0 else "-"
            html += f'<td class="{"camo-active" if is_camo else ""}">{val}{tags}</td>'
        html += f'<td style="background:#1A1A1A">{int(p_df["score"].sum())}</td>'
        html += f'<td style="background:#1A1A1A; color:#BFFF00; font-weight:bold;">{int(p_df["pts"].sum())}</td></tr>'
    st.markdown(html + "</table>", unsafe_allow_html=True)

with tab2:
    st.subheader("Tactical Resource Inventory")
    inv_data = []
    for p in PLAYERS:
        p_df = df[df['player'] == p]
        inv_data.append({
            "Player": p,
            "Camo Ball": "✅ USED" if (p_df['camo'].astype(str).str.upper() == "TRUE").any() else "Ready",
            "Mullies Used": int(pd.to_numeric(p_df['mully']).sum()),
            "Total Throws/Kicks": (p_df['throw'].astype(str).str.upper() == "TRUE").sum() + (p_df['kick'].astype(str).str.upper() == "TRUE").sum()
        })
    st.table(inv_data)

with tab3:
    h_idx = st.selectbox("Select Hole", range(1, 19))
    h_data = df[df['hole'] == h_idx]
    with st.form("hole_entry"):
        st.write(f"### Recording Hole {h_idx}")
        updates = []
        for p in PLAYERS:
            # Match current player data
            p_match = h_data[h_data['player'] == p]
            p_row = p_match.iloc[0] if not p_match.empty else {'score':0, 'drinks':0, 'camo':'FALSE', 'throw':'FALSE', 'kick':'FALSE', 'mully':0}
            
            hcp = HCP_MAP[p]
            strokes = (hcp // 18) + (1 if COURSE_IDX[h_idx-1] <= (hcp % 18) else 0)
            st.markdown(f"**{p}** (Strokes: {strokes})")
            
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            s = c1.number_input("Score", 0, 15, int(p_row['score']), key=f"s{p}{h_idx}")
            d = c2.number_input("Drinks", 0, 10, int(pd.to_numeric(p_row['drinks'] or 0)), key=f"d{p}{h_idx}")
            ca = c3.checkbox("Camo", str(p_row['camo']).upper() == "TRUE", key=f"ca{p}{h_idx}")
            th = c4.checkbox("Throw", str(p_row['throw']).upper() == "TRUE", key=f"th{p}{h_idx}")
            ki = c5.checkbox("Kick", str(p_row['kick']).upper() == "TRUE", key=f"ki{p}{h_idx}")
            mu = c6.number_input("Mully", 0, 2, int(pd.to_numeric(p_row['mully'] or 0)), key=f"mu{p}{h_idx}")
            
            # Save ALL columns (A to H) to ensure matching works
            updates.append([p, h_idx, str(s), str(d), str(ca).upper(), str(th).upper(), str(ki).upper(), str(mu)])
            
        if st.form_submit_button(f"SAVE HOLE {h_idx}"):
            if worksheet:
                # Update entire row range A to H
                start_row = ((h_idx - 1) * 5) + 2
                worksheet.update(range_name=f"A{start_row}:H{start_row+4}", values=updates)
                st.success("Hole 1 Data Saved and Synced!"); st.rerun()
