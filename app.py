import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os

# --- APP CONFIG ---
st.set_page_config(page_title="Naboom Nuut: Tactical Open", layout="wide")

# --- CSS FOR CENTERING & STYLE ---
st.markdown("""
    <style>
    .centered-header { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; margin-bottom: 20px; }
    .main-title { color: #BFFF00; font-size: 2.2rem; font-weight: 800; margin-top: 10px; }
    .sc-table { width: 100%; border-collapse: collapse; background-color: #0F0F0F; color: #EEE; font-size: 0.85rem; }
    .sc-table th, .sc-table td { border: 1px solid #2A2A2A; padding: 8px; text-align: center; }
    .camo-active { background-color: #2D3D00 !important; color: #BFFF00 !important; border: 2px solid #BFFF00 !important; }
    .power-tag { font-size: 0.6rem; display: block; margin-top: 3px; font-weight: bold; }
    .t-tag { color: #FF8C00; } .k-tag { color: #FF3E3E; } .m-tag { color: #BF00FF; }
    </style>
    """, unsafe_allow_html=True)

# --- PLAYER DATA ---
players = ["Bennie", "Adriaan", "Danie", "Martin", "Frederik"]
hcp_map = {"Bennie": 36, "Adriaan": 33, "Danie": 33, "Martin": 32, "Frederik": 32}
course_par = [4, 4, 5, 3, 5, 4, 4, 3, 4, 4, 4, 5, 3, 5, 4, 4, 3, 4]
course_idx = [17, 3, 7, 5, 9, 13, 1, 15, 11, 14, 6, 8, 18, 10, 2, 4, 16, 12]

# --- CONNECTION ENGINE ---
def get_data():
    try:
        if "connections" not in st.secrets:
            st.error("❌ 'secrets.toml' is missing the [connections] section.")
            return None, None
            
        s = st.secrets["connections"]["gsheets"]
        creds = Credentials.from_service_account_info(s, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        
        sheet_id = s["spreadsheet"].strip()
        ws = client.open_by_key(sheet_id).get_worksheet(0)
        
        raw = ws.get_all_values()
        if not raw:
            return pd.DataFrame(), ws
            
        # Standardize headers to lowercase to prevent KeyErrors
        headers = [h.strip().lower() for h in raw[0]]
        df = pd.DataFrame(raw[1:], columns=headers)
        
        # Clean numeric columns immediately
        for col in ['hole', 'score', 'drinks', 'mully']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df, ws
    except Exception as e:
        st.error(f"⚠️ Connection Error: {e}")
        return None, None

def get_points(player, hole, score, camo):
    if not score or int(score) == 0: return 0
    h_idx = int(hole) - 1
    hcp = hcp_map.get(player, 0)
    strokes = (hcp // 18) + (1 if course_idx[h_idx] <= (hcp % 18) else 0)
    net = int(score) - strokes
    pts = max(0, 2 - (net - course_par[h_idx]))
    return pts * 2 if str(camo).upper() == "TRUE" else pts

# --- APP UI ---
st.markdown('<div class="centered-header">', unsafe_allow_html=True)
if os.path.exists("Naboom logo Nuut.png"): 
    st.image("Naboom logo Nuut.png", width=120)
st.markdown('<div class="main-title">NABOOM NUUT: TACTICAL OPEN</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

df, worksheet = get_data()

# Check if data loaded. If not, don't show tabs.
if df is None:
    st.warning("The app cannot connect to your Google Sheet. Please check your Streamlit Secrets.")
    st.stop()

if df.empty:
    st.info("Database is connected but empty. Go to the **COMMAND** tab to enter the first scores.")

# --- TABS ---
t1, t2, t3 = st.tabs(["🏆 LEADERBOARD", "🎒 ARSENAL", "🎯 COMMAND"])

with t1:
    if not df.empty:
        html = '<table class="sc-table"><tr><th>PLAYER</th>' + "".join([f'<th>{h}</th>' for h in range(1, 19)]) + '<th>TOT</th><th>PTS</th></tr>'
        for p in players:
            p_df = df[df['player'].str.strip() == p].copy()
            p_df['pts'] = p_df.apply(lambda r: get_points(p, r['hole'], r['score'], r['camo']), axis=1)
            
            html += f'<tr><td style="text-align:left; font-weight:bold; padding-left:10px;">{p}</td>'
            for _, r in p_df.sort_values('hole').iterrows():
                is_camo = str(r['camo']).upper() == "TRUE"
                cls = "camo-active" if is_camo else ""
                val = int(r['score']) if r['score'] > 0 else "-"
                
                tags = ""
                if str(r['throw']).upper() == "TRUE": tags += '<span class="power-tag t-tag">THROW</span>'
                if str(r['kick']).upper() == "TRUE": tags += '<span class="power-tag k-tag">KICK</span>'
                if int(r['mully']) > 0: tags += f'<span class="power-tag m-tag">MULLY x{int(r["mully"])}</span>'
                
                html += f'<td class="{cls}">{val}{tags}</td>'
            
            html += f'<td>{int(p_df["score"].sum())}</td><td style="color:#BFFF00; font-weight:bold;">{int(p_df["pts"].sum())}</td></tr>'
        st.markdown(html + '</table>', unsafe_allow_html=True)

with t3:
    h_idx = st.selectbox("Select Hole", range(1, 19))
    # If the hole doesn't exist in the sheet yet, we create a temporary local view
    h_data = df[df['hole'] == h_idx]
    
    with st.form("entry_form"):
        updates = {}
        for p in players:
            # Find existing data or default to zeros
            existing = h_data[h_data['player'].str.strip() == p]
            p_row = existing.iloc[0] if not existing.empty else {'score':0, 'drinks':0, 'camo':'FALSE', 'throw':'FALSE', 'kick':'FALSE', 'mully':0}
            
            st.write(f"**{p}**")
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            s = c1.number_input("Score", 0, 15, int(p_row['score']), key=f"s{p}")
            d = c2.number_input("Drinks", 0, 10, int(p_row['drinks']), key=f"d{p}")
            ca = c3.checkbox("Camo", str(p_row['camo']).upper() == "TRUE", key=f"ca{p}")
            th = c4.checkbox("Throw", str(p_row['throw']).upper() == "TRUE", key=f"th{p}")
            ki = c5.checkbox("Kick", str(p_row['kick']).upper() == "TRUE", key=f"ki{p}")
            mu = c6.number_input("Mully", 0, 2, int(p_row['mully']), key=f"mu{p}")
            updates[p] = [str(s), str(d), str(ca).upper(), str(th).upper(), str(ki).upper(), str(mu)]
        
        if st.form_submit_button(f"💾 SAVE HOLE {h_idx}"):
            if worksheet:
                # Surgical Sync logic
                start_row = ((h_idx - 1) * 5) + 2
                vals = [updates[p] for p in players]
                worksheet.update(range_name=f"C{start_row}:H{start_row+4}", values=vals)
                st.success("Synced to Cloud!")
                st.rerun()
