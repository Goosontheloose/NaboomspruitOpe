import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- APP CONFIG ---
st.set_page_config(page_title="Naboom Nuut: Tactical Open", layout="wide")

# --- DATABASE CONNECTION (ROBUST VERSION) ---
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
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

def save_data(df):
    client = get_gspread_client()
    sh = client.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"])
    worksheet = sh.get_worksheet(0)
    worksheet.clear()
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    st.cache_data.clear()

# --- TOURNAMENT CONSTANTS ---
players = ["Bennie", "Adriaan", "Danie", "Martin", "Frederik"]
hcp_map = {"Bennie": 36, "Adriaan": 33, "Danie": 33, "Martin": 32, "Frederik": 32}
course_par = [4, 4, 5, 3, 5, 4, 4, 3, 4, 4, 4, 5, 3, 5, 4, 4, 3, 4]
course_idx = [17, 3, 7, 5, 9, 13, 1, 15, 11, 14, 6, 8, 18, 10, 2, 4, 16, 12]

# --- LOAD DATA ---
try:
    df = load_data()
    if df.empty: raise ValueError("Empty Sheet")
except Exception as e:
    # Create Initial Structure if sheet is empty or fails
    rows = []
    for p in players:
        for h in range(1, 19):
            rows.append({"Player": p, "Hole": h, "Score": 0, "Drinks": 0, "Camo": False, "Throw": False, "Kick": False, "Mully": 0})
    df = pd.DataFrame(rows)
    if st.button("Initialize Cloud Database"):
        save_data(df)
        st.rerun()

# --- CALCULATION LOGIC ---
def get_points(row):
    if row['Score'] == 0: return 0
    h_idx = int(row['Hole']) - 1
    hcp = hcp_map[row['Player']]
    par = course_par[h_idx]
    idx = course_idx[h_idx]
    strokes = (hcp // 18) + (1 if idx <= (hcp % 18) else 0)
    net = row['Score'] - strokes
    diff = net - par
    pts = 0
    if diff >= 2: pts = 0
    elif diff == 1: pts = 1
    elif diff == 0: pts = 2
    elif diff == -1: pts = 3
    elif diff == -2: pts = 4
    else: pts = 5
    return pts * 2 if row['Camo'] else pts

# --- UI HEADER ---
st.markdown("<h1 style='text-align: center; color: #BFFF00;'>NABOOM NUUT: TACTICAL OPEN</h1>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🏆 LEADERBOARD", "🎒 ARSENAL", "🎯 SCORE INPUT"])

with tab1:
    df['Points'] = df.apply(get_points, axis=1)
    summary = df.groupby("Player").agg({'Points': 'sum', 'Score': 'sum', 'Drinks': 'sum'}).reset_index()
    summary['Gimme (cm)'] = summary['Drinks'] * 10
    st.table(summary.sort_values("Points", ascending=False))
    if st.button("🔄 Refresh"): st.rerun()

with tab3:
    hole = st.number_input("Select Hole", 1, 18)
    for p in players:
        idx = df[(df['Player'] == p) & (df['Hole'] == hole)].index[0]
        c1, c2, c3, c4, c5, c6 = st.columns([1,1,1,1,1,1])
        df.at[idx, 'Score'] = c1.number_input(f"Score ({p})", 0, 15, value=int(df.at[idx, 'Score']), key=f"s{p}{hole}")
        df.at[idx, 'Drinks'] = c2.number_input(f"Drinks ({p})", 0, 10, value=int(df.at[idx, 'Drinks']), key=f"d{p}{hole}")
        df.at[idx, 'Camo'] = c3.checkbox("Camo", value=bool(df.at[idx, 'Camo']), key=f"c{p}{hole}")
        df.at[idx, 'Throw'] = c4.checkbox("Throw", value=bool(df.at[idx, 'Throw']), key=f"t{p}{hole}")
        df.at[idx, 'Kick'] = c5.checkbox("Kick", value=bool(df.at[idx, 'Kick']), key=f"k{p}{hole}")
        if c6.button("Mully", key=f"m{p}{hole}"): df.at[idx, 'Mully'] = 1
    
    if st.button("💾 SAVE SCORES", use_container_width=True):
        with st.spinner("Saving to Cloud..."):
            save_data(df)
            st.success("Cloud Updated!")
