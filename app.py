import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os

# --- APP CONFIG ---
st.set_page_config(page_title="Naboom Nuut: Tactical Open", layout="wide")

# --- CSS FOR PERFECT CENTERING ---
st.markdown("""
    <style>
    .centered-header {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding-bottom: 20px;
    }
    .main-title {
        color: #BFFF00;
        margin-top: 10px;
        font-size: 2.5rem;
        font-weight: bold;
    }
    .sub-title {
        color: #888;
        font-size: 1rem;
        margin-top: -10px;
    }
    .stroke-badge {
        background-color: #333;
        color: #BFFF00;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.8rem;
        margin-left: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGO HANDLING ---
logo_path = "Naboom logo Nuut.png"

# --- DATABASE CONNECTION ---
@st.cache_resource
def get_gspread_client():
    s = st.secrets["connections"]["gsheets"]
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(s, scopes=scopes)
    return gspread.authorize(creds)

def load_data():
    client = get_gspread_client()
    sh = client.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"])
    worksheet = sh.get_worksheet(0)
    return pd.DataFrame(worksheet.get_all_records())

def save_data(df):
    client = get_gspread_client()
    sh = client.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"])
    worksheet = sh.get_worksheet(0)
    worksheet.clear()
    df_filled = df.fillna(0)
    worksheet.update([df_filled.columns.values.tolist()] + df_filled.values.tolist())
    st.cache_data.clear()

# --- CONSTANTS ---
players = ["Bennie", "Adriaan", "Danie", "Martin", "Frederik"]
hcp_map = {"Bennie": 36, "Adriaan": 33, "Danie": 33, "Martin": 32, "Frederik": 32}
course_par = [4, 4, 5, 3, 5, 4, 4, 3, 4, 4, 4, 5, 3, 5, 4, 4, 3, 4]
course_idx = [17, 3, 7, 5, 9, 13, 1, 15, 11, 14, 6, 8, 18, 10, 2, 4, 16, 12]

# --- LOAD DATA ---
try:
    df = load_data()
    if df.empty: raise ValueError
except Exception:
    rows = []
    for p in players:
        for h in range(1, 19):
            rows.append({"Player": p, "Hole": h, "Score": 0, "Drinks": 0, "Camo": False, "Throw": False, "Kick": False, "Mully": 0})
    df = pd.DataFrame(rows)

# --- CALCULATE STROKES PER HOLE ---
def get_allowed_strokes(player, hole_num):
    hcp = hcp_map[player]
    idx = course_idx[hole_num - 1]
    return (hcp // 18) + (1 if idx <= (hcp % 18) else 0)

# --- SCORING LOGIC ---
def get_points(row):
    if row['Score'] == 0: return 0
    h_idx = int(row['Hole']) - 1
    par = course_par[h_idx]
    strokes = get_allowed_strokes(row['Player'], int(row['Hole']))
    net = row['Score'] - strokes
    pts = max(0, 2 - (net - par))
    return pts * 2 if row['Camo'] else pts

# --- CENTERED HEADER ---
st.markdown('<div class="centered-header">', unsafe_allow_html=True)
if os.path.exists(logo_path):
    st.image(logo_path, width=200)
st.markdown('<p class="main-title">NABOOM NUUT: TACTICAL OPEN</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Sole Scorekeeper Portal | Tactical Resource Management</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["🏆 LEADERBOARD", "🎒 THE ARSENAL", "🎯 HOLE COMMAND"])

with tab1:
    df['Points'] = df.apply(get_points, axis=1)
    summary = df.groupby("Player").agg({'Points': 'sum', 'Score': 'sum', 'Drinks': 'sum'}).reset_index()
    summary['Gimme (cm)'] = summary['Drinks'] * 10
    st.subheader("Current Standings")
    st.dataframe(summary.sort_values("Points", ascending=False), use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Tactical Resource Inventory")
    # ... (Same Arsenal logic as before)
    arsenal = []
    for p in players:
        p_data = df[df['Player'] == p]
        arsenal.append({
            "Player": p,
            "Camo Used": p_data['Camo'].sum(),
            "Throws (1-9)": p_data[p_data['Hole'] <= 9]['Throw'].sum(),
            "Throws (10-18)": p_data[p_data['Hole'] > 9]['Throw'].sum(),
            "Kicks (1-9)": p_data[p_data['Hole'] <= 9]['Kick'].sum(),
            "Kicks (10-18)": p_data[p_data['Hole'] > 9]['Kick'].sum(),
            "Mullies Used": p_data['Mully'].sum()
        })
    st.table(pd.DataFrame(arsenal))

with tab3:
    hole_to_edit = st.selectbox("Select Hole", range(1, 19))
    h_idx = hole_to_edit - 1
    st.markdown(f"### Hole {hole_to_edit} (Par {course_par[h_idx]} | Index {course_idx[h_idx]})")
    
    with st.form("score_entry_form"):
        temp_df = df.copy()
        for p in players:
            idx = temp_df[(temp_df['Player'] == p) & (temp_df['Hole'] == hole_to_edit)].index[0]
            
            # CALCULATE STROKES FOR DISPLAY
            strokes = get_allowed_strokes(p, hole_to_edit)
            st.markdown(f"**{p}** <span class='stroke-badge'>Strokes: {strokes}</span>", unsafe_allow_html=True)
            
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            temp_df.at[idx, 'Score'] = c1.number_input("Score", 0, 15, value=int(df.at[idx, 'Score']), key=f"s_{p}_{hole_to_edit}")
            temp_df.at[idx, 'Drinks'] = c2.number_input("Drinks", 0, 10, value=int(df.at[idx, 'Drinks']), key=f"d_{p}_{hole_to_edit}")
            temp_df.at[idx, 'Camo'] = c3.checkbox("Camo", value=bool(df.at[idx, 'Camo']), key=f"c_{p}_{hole_to_edit}")
            temp_df.at[idx, 'Throw'] = c4.checkbox("Throw", value=bool(df.at[idx, 'Throw']), key=f"t_{p}_{hole_to_edit}")
            temp_df.at[idx, 'Kick'] = c5.checkbox("Kick", value=bool(df.at[idx, 'Kick']), key=f"k_{p}_{hole_to_edit}")
            temp_df.at[idx, 'Mully'] = c6.number_input("Mully", 0, 2, value=int(df.at[idx, 'Mully']), key=f"m_{p}_{hole_to_edit}")
            st.divider()

        if st.form_submit_button("💾 SYNC SCORES TO CLOUD", use_container_width=True):
            save_data(temp_df)
            st.success(f"Hole {hole_to_edit} data secured!")
            st.rerun()
