import streamlit as st
import pandas as pd
import gspread
import os
import base64
from google.oauth2.service_account import Credentials

# --- APP CONFIG ---
st.set_page_config(page_title="Naboom Nuut: Tactical Open", layout="wide")

# Initialize Reset Counter to force UI refresh
if 'reset_id' not in st.session_state:
    st.session_state.reset_id = 0

# Function to safely load local image as Base64 (Best for Mobile/Cloud)
def get_base64_image(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return None

# --- UI STYLING ---
st.markdown("""
    <style>
    /* Responsive Header Container */
    .header-box {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 10px 0;
        width: 100%;
        pointer-events: auto;
    }
    
    .main-title { 
        color: #BFFF00; 
        font-size: 1.8rem; /* Scaled down for mobile */
        font-weight: 800; 
        text-transform: uppercase; 
        margin-top: 10px; 
        margin-bottom: 5px;
        letter-spacing: 1px; 
    }
    
    /* Force Tabs to stay on top and clickable */
    .stTabs [data-baseweb="tab-list"] {
        z-index: 1000 !important;
        position: relative;
    }

    /* Mobile Scroll Container for Tables */
    .scroll-wrapper {
        width: 100%;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        margin-top: 10px;
    }

    /* Ranking Table Styling */
    .rank-table { width: 100%; border-collapse: collapse; background-color: #0F0F0F; }
    .rank-table th { background-color: #1A1A1A; color: #BFFF00; padding: 10px; text-align: left; border-bottom: 2px solid #333; font-size: 0.8rem; }
    .rank-table td { padding: 10px; border-bottom: 1px solid #222; color: #EEE; font-size: 0.9rem; }
    .rank-1 { color: #FFD700; font-weight: bold; border-left: 5px solid #FFD700; }
    .pts-highlight { color: #BFFF00; font-weight: 800; }
    .gimme-highlight { color: #00D1FF; font-size: 0.8rem; }

    /* Scorecard Grid */
    .sc-table { min-width: 800px; border-collapse: collapse; background-color: #0F0F0F; color: #EEE; font-size: 0.7rem; table-layout: fixed; }
    .sc-table th, .sc-table td { border: 1px solid #333; padding: 6px 2px; text-align: center; vertical-align: middle; }
    .sc-table th { background-color: #1A1A1A; color: #BFFF00; font-size: 0.6rem; }
    
    .player-cell { text-align: left !important; font-weight: bold; background: #151515; padding-left: 8px !important; width: 90px !important; color: #FFF; border-left: 4px solid #BFFF00 !important; }
    .score-val { font-size: 0.8rem; font-weight: 700; color: #FFF; }
    .pts-val { font-size: 0.8rem; font-weight: 800; color: #BFFF00; }
    .divider { color: #555; margin: 0 2px; }
    
    .tag-container { display: flex; flex-wrap: wrap; justify-content: center; gap: 2px; margin-top: 3px; min-height: 10px; }
    .p-tag { font-size: 0.5rem; font-weight: 900; padding: 1px 2px; border-radius: 2px; text-transform: uppercase; line-height: 1; }
    
    .t-tag { color: #FF8C00; border: 1px solid #FF8C00; } 
    .k-tag { color: #FF3E3E; border: 1px solid #FF3E3E; } 
    .m-tag { color: #BF00FF; border: 1px solid #BF00FF; } 
    .me-tag { color: #00D1FF; border: 1px solid #00D1FF; background: rgba(0, 209, 255, 0.2); }
    .ld-tag { color: #00FFCC; border: 1px solid #00FFCC; }
    .cp-tag { color: #FFCC00; border: 1px solid #FFCC00; }
    
    .camo-active { background-color: #1E2B00 !important; border: 1px solid #BFFF00 !important; }
    .total-box { background: #1A1A1A; font-weight: bold; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

# --- CONSTANTS ---
LOCAL_LOGO = "Naboom logo Nuut.png"
PLAYERS = ["Bennie", "Adriaan", "Danie", "Martin", "Frederik"]
HCP_MAP = {"BENNIE": 36, "ADRIAAN": 33, "DANIE": 33, "MARTIN": 32, "FREDERIK": 32}
COURSE_PAR = [4, 4, 5, 3, 5, 4, 4, 3, 4, 4, 4, 5, 3, 5, 4, 4, 3, 4]
COURSE_IDX = [17, 3, 7, 5, 9, 13, 1, 15, 11, 14, 6, 8, 18, 10, 2, 4, 16, 12]

# --- DATABASE ENGINE ---
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
    pts = max
