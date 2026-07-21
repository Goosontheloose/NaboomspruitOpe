import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from urllib.parse import quote

# --- APP CONFIG & LOGO ---
st.set_page_config(page_title="Naboom Nuut: Tactical Open", layout="wide")

# Handle Logo URL Encoding
logo_filename = "Naboom logo Nuut.png"
safe_logo_url = f"https://raw.githubusercontent.com/{st.secrets.get('github_username', 'YOUR_GITHUB_USERNAME')}/{st.secrets.get('github_repo', 'YOUR_REPO_NAME')}/main/{quote(logo_filename)}"

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
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
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
except:
    rows = []
    for p in players:
        for h in range(1, 19):
            rows.append({"Player": p, "Hole": h, "Score": 0, "Drinks": 0, "Camo": False, "Throw": False, "Kick": False, "Mully": 0})
    df = pd.DataFrame(rows)

# --- SCORING LOGIC ---
def get_points(row):
    if row['Score'] == 0: return 0
    h_idx = int(row['Hole']) - 1
    hcp = hcp_map[row['Player']]
    par = course_par[h_idx]
    idx = course_idx[h_idx]
    strokes = (hcp // 18) + (1 if idx <= (hcp % 18) else 0)
    net = row['Score'] - strokes
    pts = max(0, 2 - (net - par))
    return pts * 2 if row['Camo'] else pts

# --- UI DISPLAY ---
col1, col2 = st.columns([1, 4])
with col1:
    st.image(safe_logo_url, width=150)
with col2:
    st.markdown("<h1 style='color: #BFFF00; margin-top: 10px;'>NABOOM NUUT: TACTICAL OPEN</h1>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🏆 LEADERBOARD", "🎒 THE ARSENAL", "🎯 HOLE COMMAND"])

with tab1:
    df['Points'] = df.apply(get_points, axis=1)
    summary = df.groupby("Player").agg({'Points': 'sum', 'Score': 'sum', 'Drinks': 'sum'}).reset_index()
    summary['Gimme (cm)'] = summary['Drinks'] * 10
    st.dataframe(summary.sort_values("Points", ascending=False), use_container_width=True)

with tab2:
    st.subheader("Tactical Resource Tracking")
    arsenal = []
    for p in players:
        p_data = df[df['Player'] == p]
        arsenal.append({
            "Player": p,
