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
            "Camo Used": p_data['Camo'].sum(),
            "Throws (Out)": p_data[p_data['Hole'] <= 9]['Throw'].sum(),
            "Throws (In)": p_data[p_data['Hole'] > 9]['Throw'].sum(),
            "Kicks (Out)": p_data[p_data['Hole'] <= 9]['Kick'].sum(),
            "Kicks (In)": p_data[p_data['Hole'] > 9]['Kick'].sum(),
            "Mullies": p_data['Mully'].sum()
        })
    st.table(pd.DataFrame(arsenal))

with tab3:
    hole = st.selectbox("Select Hole", range(1, 19))
    st.info(f"Par: {course_par[hole-1]} | Index: {course_idx[hole-1]}")
    
    with st.form("score_form"):
        for p in players:
            idx = df[(df['Player'] == p) & (df['Hole'] == hole)].index[0]
            st.markdown(f"**{p}**")
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            df.at[idx, 'Score'] = c1.number_input("Strokes", 0, 15, value=int(df.at[idx, 'Score']), key=f"s{p}")
            df.at[idx, 'Drinks'] = c2.number_input("Drinks", 0, 10, value=int(df.at[idx, 'Drinks']), key=f"d{p}")
            df.at[idx, 'Camo'] = c3.checkbox("Camo", value=bool(df.at[idx, 'Camo']), key=f"c{p}")
            df.at[idx, 'Throw'] = c4.checkbox("Throw", value=bool(df.at[idx, 'Throw']), key=f"t{p}")
            df.at[idx, 'Kick'] = c5.checkbox("Kick", value=bool(df.at[idx, 'Kick']), key=f"k{p}")
            df.at[idx, 'Mully'] = c6.number_input("Mully", 0, 2, value=int(df.at[idx, 'Mully']), key=f"m{p}")
        
        if st.form_submit_state("Save Data"):
            save_data(df)
            st.success("Scores Synced to Cloud!")
            st.rerun()
