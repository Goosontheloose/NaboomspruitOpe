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
    .sc-table { width: 100%; border-collapse: collapse; background-color: #0F0F0F; color: #EEE; font-size: 0.75rem; table-layout: fixed; }
    .sc-table th, .sc-table td { border: 1px solid #333; padding: 6px 2px; text-align: center; overflow: hidden; }
    .sc-table th { background-color: #1A1A1A; color: #BFFF00; font-size: 0.7rem; }
    .player-cell { text-align: left !important; font-weight: bold; background: #151515; padding-left: 8px !important; width: 90px !important; color: #FFF; border-left: 4px solid #BFFF00 !important; }
    .score-val { font-size: 0.85rem; font-weight: 700; color: #FFF; }
    .pts-val { font-size: 0.8rem; font-weight: 800; color: #BFFF00; }
    .divider { color: #444; margin: 0 2px; }
    .camo-active { background-color: #1E2B00 !important; border: 1px solid #BFFF00 !important; }
    .power-icon { font-size: 0.5rem; display: block; font-weight: 900; margin-top: 2px; line-height: 1.1; text-transform: uppercase; }
    .t-tag { color: #FF8C00; } .k-tag { color: #FF3E3E; } .m-tag { color: #BF00FF; } .me-tag { color: #00D1FF; }
    .d-tag { color: #00FFCC; border: 1px solid #00FFCC; padding: 0 1px; border-radius: 2px; } /* Longest Drive */
    .c-tag { color: #FFCC00; border: 1px solid #FFCC00; padding: 0 1px; border-radius: 2px; } /* Closest Pin */
    .total-box { background: #1A1A1A; font-weight: bold; font-size: 0.9rem; }
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
        data = ws.get_all_values()
        if len(data) < 2: return pd.DataFrame(), ws
        df_cloud = pd.DataFrame(data[1:], columns=[c.lower().strip() for c in data[0]])
        return df_cloud, ws
    except Exception as e:
        return pd.DataFrame(), None

def get_master_df(df_cloud):
    rows = []
    # New Column 'honor' added for Longest Drive / Closest Pin
    for h in range(1, 19):
        for p in PLAYERS:
            rows.append({"player": p, "hole": h, "score": 0, "drinks": 0, "camo": "FALSE", "throw": "FALSE", "kick": "FALSE", "mully": 0, "me2": "FALSE", "honor": "NONE"})
    master = pd.DataFrame(rows)
    
    if not df_cloud.empty:
        master['hole'] = master['hole'].astype(str)
        master['player'] = master['player'].astype(str).str.strip().str.upper()
        df_cloud['hole'] = df_cloud['hole'].astype(str)
        df_cloud['player'] = df_cloud['player'].astype(str).str.strip().str.upper()
        
        master = master.merge(df_cloud, on=['player', 'hole'], how='left', suffixes=('', '_c'))
        cols = ['score', 'drinks', 'camo', 'throw', 'kick', 'mully', 'me2', 'honor']
        for col in cols:
            if f"{col}_c" in master.columns:
                master[col] = master[f"{col}_c"].combine_first(master[col])
        master = master[["player", "hole"] + cols]

    master['score'] = pd.to_numeric(master['score'], errors='coerce').fillna(0).astype(int)
    master['hole'] = pd.to_numeric(master['hole']).astype(int)
    name_map = {p.upper(): p for p in PLAYERS}
    master['player'] = master['player'].map(name_map)
    return master

def calculate_hole_points(p, h, score, camo):
    if score == 0: return 0
    h_idx = int(h) - 1
    par = COURSE_PAR[h_idx]
    hcp = HCP_MAP.get(p, 0)
    h_strokes = (hcp // 18) + (1 if COURSE_IDX[h_idx] <= (hcp % 18) else 0)
    net = score - h_strokes
    pts = max(0, 2 - (net - par))
    if pts > 0 and par in [3, 5]: pts += 1 # Par 3/5 Bonus
    return pts * 2 if str(camo).upper() == "TRUE" else pts

# --- HEADER ---
st.markdown(f'<div class="header-container"><img src="{LOGO_URL}" width="120"><div class="main-title">Naboom Nuut: Tactical Open</div></div>', unsafe_allow_html=True)

df_raw, worksheet = get_database()
df = get_master_df(df_raw)

tab1, tab2, tab3 = st.tabs(["🏆 LIVE SCORECARD", "🎒 THE ARSENAL", "🎯 HOLE COMMAND"])

with tab1:
    df['pts'] = df.apply(lambda r: calculate_hole_points(r['player'], r['hole'], r['score'], r['camo']), axis=1)
    html = '<table class="sc-table"><tr><th style="width:90px">PLAYER</th>'
    for h in range(1, 19):
        html += f'<th>H{h}<br><span style="color:#666; font-size:0.6rem">P{COURSE_PAR[h-1]}</span></th>'
    html += '<th class="total-box">TOT</th><th class="total-box" style="color:#BFFF00">PTS</th></tr>'
    
    for p in PLAYERS:
        p_df = df[df['player'] == p].sort_values('hole')
        html += f'<tr><td class="player-cell">{p}</td>'
        for _, r in p_df.iterrows():
            is_camo = str(r['camo']).upper() == "TRUE"
            cls = "camo-active" if is_camo else ""
            s_disp = int(r['score']) if r['score'] > 0 else "-"
            p_disp = int(r['pts']) if r['score'] > 0 else "-"
            
            # Honors display
            h_tag = ""
            if str(r['honor']).upper() == "D": h_tag = '<span class="d-tag">D</span>'
            if str(r['honor']).upper() == "C": h_tag = '<span class="c-tag">C</span>'
            
            tags = "".join([
                f'<span class="power-icon t-tag">T</span>' if str(r['throw']).upper() == "TRUE" else "",
                f'<span class="power-icon k-tag">K</span>' if str(r['kick']).upper() == "TRUE" else "",
                f'<span class="power-icon m-tag">M</span>' if int(pd.to_numeric(r['mully'] or 0)) > 0 else "",
                f'<span class="power-icon me-tag">ME</span>' if str(r['me2']).upper() == "TRUE" else "",
                h_tag
            ])
            html += f'<td class="{cls}"><span class="score-val">{s_disp}</span><span class="divider">|</span><span class="pts-val">{p_disp}</span>{tags}</td>'
        html += f'<td class="total-box">{int(p_df["score"].sum())}</td>'
        html += f'<td class="total-box" style="color:#BFFF00">{int(p_df["pts"].sum())}</td></tr>'
    st.markdown(html + "</table>", unsafe_allow_html=True)
    st.caption("Legend: T=Throw | K=Kick | M=Mully | ME=Me2 | D=Longest Drive | C=Closest Pin")

with tab2:
    st.subheader("Tactical Resource Inventory")
    inv = []
    for p in PLAYERS:
        p_df = df[df['player'] == p]
        inv.append({
            "Player": p,
            "Camo Ball": "✅ USED" if (p_df['camo'].astype(str).str.upper() == "TRUE").any() else "READY",
            "Me2": "✅ USED" if (p_df['me2'].astype(str).str.upper() == "TRUE").any() else "READY",
            "Mullies": f"{int(pd.to_numeric(p_df['mully']).sum())} / 2",
            "Throws": (p_df['throw'].astype(str).str.upper() == "TRUE").sum(),
            "Kicks": (p_df['kick'].astype(str).str.upper() == "TRUE").sum(),
            "Drives (D)": (p_df['honor'].astype(str).str.upper() == "D").sum(),
            "Pins (C)": (p_df['honor'].astype(str).str.upper() == "C").sum()
        })
    st.table(inv)

with tab3:
    h_idx = st.selectbox("Select Hole", range(1, 19))
    h_data = df[df['hole'] == h_idx]
    par_val = COURSE_PAR[h_idx-1]
    
    with st.form("hole_entry"):
        st.info(f"Hole {h_idx} | Par {par_val} | Index {COURSE_IDX[h_idx-1]}")
        updates = []
        for p in PLAYERS:
            p_row = h_data[h_data['player'] == p].iloc[0]
            h_strokes = (HCP_MAP[p] // 18) + (1 if COURSE_IDX[h_idx-1] <= (HCP_MAP[p] % 18) else 0)
            st.markdown(f"**{p}** (+{h_strokes} strokes)")
            
            # Layout with 8 columns to accommodate the Honor checkbox
            cols = st.columns([1, 1, 1, 1, 1, 1, 1, 1.2])
            s = cols[0].number_input("Score", 0, 15, int(p_row['score']), key=f"s{p}")
            d = cols[1].number_input("Drink", 0, 10, int(pd.to_numeric(p_row['drinks'] or 0)), key=f"d{p}")
            ca = cols[2].checkbox("Camo", str(p_row['camo']).upper() == "TRUE", key=f"ca{p}")
            th = cols[3].checkbox("Thr", str(p_row['throw']).upper() == "TRUE", key=f"th{p}")
            ki = cols[4].checkbox("Kck", str(p_row['kick']).upper() == "TRUE", key=f"ki{p}")
            mu = cols[5].number_input("Mly", 0, 1, int(pd.to_numeric(p_row['mully'] or 0)), key=f"mu{p}")
            me = cols[6].checkbox("Me2", str(p_row['me2']).upper() == "TRUE", key=f"me{p}")
            
            # Logic for Longest Drive (Par 5) or Closest Pin (Par 3)
            honor_val = "NONE"
            if par_val == 5:
                if cols[7].checkbox("Drive (D)", str(p_row['honor']).upper() == "D", key=f"honor{p}"): honor_val = "D"
            elif par_val == 3:
                if cols[7].checkbox("Pin (C)", str(p_row['honor']).upper() == "C", key=f"honor{p}"): honor_val = "C"
            else:
                cols[7].write("---") # Par 4s have no special honor
                
            updates.append([p, h_idx, str(s), str(d), str(ca).upper(), str(th).upper(), str(ki).upper(), str(mu), str(me).upper(), honor_val])
            
        if st.form_submit_button(f"SAVE HOLE {h_idx}"):
            if worksheet:
                start_row = ((h_idx - 1) * 5) + 2
                worksheet.update(range_name=f"A{start_row}:J{start_row+4}", values=updates)
                st.success(f"Hole {h_idx} Updated."); st.rerun()
