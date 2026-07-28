import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- APP CONFIG ---
st.set_page_config(page_title="Naboom Nuut: Tactical Open", layout="wide")

# --- UI STYLING ---
st.markdown("""
    <style>
    .header-container { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; margin-bottom: 20px; }
    .main-title { color: #BFFF00; font-size: 2.2rem; font-weight: 800; text-transform: uppercase; margin-top: 10px; letter-spacing: 2px; }
    
    /* Scorecard Grid */
    .sc-table { width: 100%; border-collapse: collapse; background-color: #0F0F0F; color: #EEE; font-size: 0.75rem; table-layout: fixed; }
    .sc-table th, .sc-table td { border: 1px solid #333; padding: 6px 2px; text-align: center; vertical-align: middle; }
    .sc-table th { background-color: #1A1A1A; color: #BFFF00; font-size: 0.6rem; line-height: 1.2; }
    
    .player-cell { text-align: left !important; font-weight: bold; background: #151515; padding-left: 8px !important; width: 90px !important; color: #FFF; border-left: 4px solid #BFFF00 !important; }
    
    .score-val { font-size: 0.85rem; font-weight: 700; color: #FFF; }
    .pts-val { font-size: 0.8rem; font-weight: 800; color: #BFFF00; }
    .divider { color: #444; margin: 0 2px; }
    
    /* Powerup Tags - Fixed for ME visibility */
    .tag-container { display: flex; flex-wrap: wrap; justify-content: center; gap: 2px; margin-top: 3px; }
    .p-tag { font-size: 0.5rem; font-weight: 900; padding: 1px 2px; border-radius: 2px; text-transform: uppercase; line-height: 1; }
    
    .t-tag { color: #FF8C00; border: 1px solid #FF8C00; } 
    .k-tag { color: #FF3E3E; border: 1px solid #FF3E3E; } 
    .m-tag { color: #BF00FF; border: 1px solid #BF00FF; } 
    .me-tag { color: #00D1FF; border: 1px solid #00D1FF; background: rgba(0, 209, 255, 0.2); display: inline-block !important; }
    .d-tag { color: #00FFCC; border: 1px solid #00FFCC; background: rgba(0, 255, 204, 0.1); }
    .c-tag { color: #FFCC00; border: 1px solid #FFCC00; background: rgba(255, 204, 0, 0.1); }
    
    .camo-active { background-color: #1E2B00 !important; border: 1px solid #BFFF00 !important; }
    .total-box { background: #1A1A1A; font-weight: bold; font-size: 0.85rem; }
    </style>
    """, unsafe_allow_html=True)

# --- CONSTANTS ---
LOGO_URL = "https://d2yln88910ulu4.cloudfront.net/chatFiles/c210e3f7-57b2-4ff7-833e-889a87dd3520.png"
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
        df_cloud = pd.DataFrame(data[1:], columns=[c.lower().strip() for c in data[0]])
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

# --- UI ---
st.markdown(f'<div class="header-container"><img src="{LOGO_URL}" width="120"><div class="main-title">Naboom Nuut: Tactical Open</div></div>', unsafe_allow_html=True)

df_raw, worksheet = get_database()
df = get_master_df(df_raw)

tab1, tab2, tab3 = st.tabs(["🏆 LIVE SCORECARD", "🎒 THE ARSENAL", "🎯 HOLE COMMAND"])

with tab1:
    df['pts'] = df.apply(lambda r: calculate_points(r['player'], r['hole'], r['score'], r['camo']), axis=1)
    html = '<table class="sc-table"><tr><th style="width:90px">PLAYER</th>'
    for h in range(1, 19):
        html += f'<th>H{h}<br><span style="color:#666">P{COURSE_PAR[h-1]}</span></th>'
    html += '<th class="total-box">TOT</th><th class="total-box" style="color:#BFFF00">PTS</th></tr>'
    
    for p in PLAYERS:
        p_df = df[df['player_disp'] == p].sort_values('hole')
        html += f'<tr><td class="player-cell">{p}</td>'
        for _, r in p_df.iterrows():
            is_camo = str(r['camo']).upper() == "TRUE"
            is_me2 = str(r['me2']).upper() == "TRUE"
            
            # Tags
            tags = []
            if str(r['throw']).upper() == "TRUE": tags.append('<span class="p-tag t-tag">T</span>')
            if str(r['kick']).upper() == "TRUE": tags.append('<span class="p-tag k-tag">K</span>')
            if int(r['mully']) > 0: tags.append('<span class="p-tag m-tag">M</span>')
            if is_me2: tags.append('<span class="p-tag me-tag">ME</span>')
            if str(r['honor']).upper() == "D": tags.append('<span class="p-tag d-tag">D</span>')
            if str(r['honor']).upper() == "C": tags.append('<span class="p-tag c-tag">C</span>')
            
            tag_html = f'<div class="tag-container">{"".join(tags)}</div>' if tags else ""
            s_val = int(r['score']) if r['score'] > 0 else "-"
            p_val = int(r['pts']) if r['score'] > 0 else "-"
            
            html += f'<td class="{"camo-active" if is_camo else ""}"><span class="score-val">{s_val}</span><span class="divider">|</span><span class="pts-val">{p_val}</span>{tag_html}</td>'
        
        html += f'<td class="total-box">{int(p_df["score"].sum())}</td>'
        html += f'<td class="total-box" style="color:#BFFF00">{int(p_df["pts"].sum())}</td></tr>'
    st.markdown(html + "</table>", unsafe_allow_html=True)

with tab2:
    st.subheader("Tactical Resource Inventory")
    inv = []
    for p in PLAYERS:
        p_df = df[df['player_disp'] == p]
        camo_used = (p_df['camo'].astype(str).str.upper() == "TRUE").sum()
        me2_used = (p_df['me2'].astype(str).str.upper() == "TRUE").any()
        
        inv.append({
            "Player": p,
            "Camo Balls": f"Used {camo_used} / 2",
            "Camo Status": "✅ READY" if camo_used < 2 else "❌ EMPTY",
            "Me2": "✅ USED" if me2_used else "READY",
            "Mullies": f"{int(p_df['mully'].sum())} / 2",
            "Throws": (p_df['throw'].astype(str).str.upper() == "TRUE").sum(),
            "Kicks": (p_df['kick'].astype(str).str.upper() == "TRUE").sum()
        })
    st.table(inv)

with tab3:
    h_idx = st.selectbox("Select Hole", range(1, 19))
    par_val = COURSE_PAR[h_idx-1]
    
    if st.button("🚨 RESET HOLE DATA", use_container_width=True):
        if worksheet:
            reset = [[p, str(h_idx), "0", "0", "FALSE", "FALSE", "FALSE", "0", "FALSE", "NONE"] for p in PLAYERS]
            worksheet.update(range_name=f"A{((h_idx-1)*5)+2}:J{((h_idx-1)*5)+6}", values=reset)
            st.rerun()

    h_data = df[df['hole'] == h_idx]
    with st.form("entry"):
        st.info(f"Hole {h_idx} | Par {par_val}")
        updates = []
        for p in PLAYERS:
            try: p_row = h_data[h_data['player'] == p.upper()].iloc[0]
            except: p_row = {"score":0, "drinks":0, "camo":"FALSE", "throw":"FALSE", "kick":"FALSE", "mully":0, "me2":"FALSE", "honor":"NONE"}

            st.markdown(f"**{p}**")
            c = st.columns([1, 1, 1, 1, 1, 1, 1, 1.2])
            s = c[0].number_input("Score", 0, 15, int(p_row['score']), key=f"s_{p}")
            d = c[1].number_input("Drink", 0, 10, int(p_row['drinks']), key=f"d_{p}")
            ca = c[2].checkbox("Camo", str(p_row['camo']).upper() == "TRUE", key=f"ca_{p}")
            th = c[3].checkbox("Thr", str(p_row['throw']).upper() == "TRUE", key=f"th_{p}")
            ki = c[4].checkbox("Kck", str(p_row['kick']).upper() == "TRUE", key=f"ki_{p}")
            mu = c[5].number_input("Mly", 0, 1, int(p_row['mully']), key=f"mu_{p}")
            me = c[6].checkbox("Me2", str(p_row['me2']).upper() == "TRUE", key=f"me_{p}")
            
            h_val = "NONE"
            if par_val == 5:
                if c[7].checkbox("Drive", str(p_row['honor']).upper() == "D", key=f"hd_{p}"): h_val = "D"
            elif par_val == 3:
                if c[7].checkbox("Pin", str(p_row['honor']).upper() == "C", key=f"hc_{p}"): h_val = "C"
                
            updates.append([p, str(h_idx), str(s), str(d), str(ca).upper(), str(th).upper(), str(ki).upper(), str(mu), str(me).upper(), h_val])
            
        if st.form_submit_button(f"SAVE HOLE {h_idx}"):
            if worksheet:
                worksheet.update(range_name=f"A{((h_idx-1)*5)+2}:J{((h_idx-1)*5)+6}", values=updates)
                st.success("Synced!"); st.rerun()
