import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from urllib.parse import quote

# --- APP CONFIG & LOGO ---
st.set_page_config(page_title="Naboom Nuut: Tactical Open", layout="wide")

# Logo configuration
# If the logo is in your GitHub repo, this will find it.
logo_filename = "Naboom logo Nuut.png"
github_user = st.secrets.get("github_username", "YOUR_GITHUB_USERNAME")
github_repo = st.secrets.get("github_repo", "YOUR_REPO_NAME")
safe_logo_url = f"https://raw.githubusercontent.com/{github_user}/{github_repo}/main/{quote(logo_filename)}"

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
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

def save_data(df):
    client = get_gspread_client()
    sh = client.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"])
    worksheet = sh.get_worksheet(0)
    worksheet.clear()
    # Handle NaN values to prevent JSON errors
    df_filled = df.fillna(0)
    worksheet.update([df_filled.columns.values.tolist()] + df_filled.values.tolist())
    st.cache_data.clear()

# --- TOURNAMENT CONSTANTS ---
players = ["Bennie", "Adriaan", "Danie", "Martin", "Frederik"]
hcp_map = {"Bennie": 36, "Adriaan": 33, "Danie": 33, "Martin": 32, "Frederik": 32}
course_par = [4, 4, 5, 3, 5, 4, 4, 3, 4, 4, 4, 5, 3, 5, 4, 4, 3, 4]
course_idx = [17, 3, 7, 5, 9, 13, 1, 15, 11, 14, 6, 8, 18, 10, 2, 4, 16, 12]

# --- LOAD DATA ---
try:
    df = load_data()
    if df.empty: raise ValueError
except Exception:
    # Initial data structure if sheet is empty
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
    # Calculate strokes given based on hole index
    strokes = (hcp // 18) + (1 if idx <= (hcp % 18) else 0)
    net = row['Score'] - strokes
    pts = max(0, 2 - (net - par))
    return pts * 2 if row['Camo'] else pts

# --- UI LAYOUT ---
col1, col2 = st.columns([1, 5])
with col1:
    st.image(safe_logo_url, width=120)
with col2:
    st.markdown("<h1 style='color: #BFFF00; margin-bottom: 0;'>NABOOM NUUT: TACTICAL OPEN</h1>", unsafe_allow_html=True)
    st.caption("Sole Scorekeeper Portal | Real-time Cloud Sync")

tab1, tab2, tab3 = st.tabs(["🏆 LEADERBOARD", "🎒 THE ARSENAL", "🎯 HOLE COMMAND"])

with tab1:
    df['Points'] = df.apply(get_points, axis=1)
    summary = df.groupby("Player").agg({'Points': 'sum', 'Score': 'sum', 'Drinks': 'sum'}).reset_index()
    summary['Gimme (cm)'] = summary['Drinks'] * 10
    st.subheader("Current Standings")
    st.dataframe(summary.sort_values("Points", ascending=False), use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Tactical Resource Inventory")
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
    st.info("Limits: Me2 (1/game) | Throws/Kicks (1 per 9 holes) | Mulligans (2 per 18 holes)")

with tab3:
    hole_to_edit = st.selectbox("Select Hole to Record", range(1, 19))
    st.markdown(f"### Hole {hole_to_edit} (Par {course_par[hole_to_edit-1]} | Index {course_idx[hole_to_edit-1]})")
    
    # Use a form to batch the updates
    with st.form("score_entry_form"):
        # We need to keep a temporary copy of the edits to apply on submit
        temp_df = df.copy()
        
        for p in players:
            idx = temp_df[(temp_df['Player'] == p) & (temp_df['Hole'] == hole_to_edit)].index[0]
            st.markdown(f"**{p}**")
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            
            temp_df.at[idx, 'Score'] = c1.number_input("Score", 0, 15, value=int(df.at[idx, 'Score']), key=f"s_{p}_{hole_to_edit}")
            temp_df.at[idx, 'Drinks'] = c2.number_input("Drinks", 0, 10, value=int(df.at[idx, 'Drinks']), key=f"d_{p}_{hole_to_edit}")
            temp_df.at[idx, 'Camo'] = c3.checkbox("Camo", value=bool(df.at[idx, 'Camo']), key=f"c_{p}_{hole_to_edit}")
            temp_df.at[idx, 'Throw'] = c4.checkbox("Throw", value=bool(df.at[idx, 'Throw']), key=f"t_{p}_{hole_to_edit}")
            temp_df.at[idx, 'Kick'] = c5.checkbox("Kick", value=bool(df.at[idx, 'Kick']), key=f"k_{p}_{hole_to_edit}")
            temp_df.at[idx, 'Mully'] = c6.number_input("Mully", 0, 2, value=int(df.at[idx, 'Mully']), key=f"m_{p}_{hole_to_edit}")
            st.divider()

        submit = st.form_submit_button("💾 SYNC SCORES TO CLOUD", use_container_width=True)
        
        if submit:
            with st.spinner("Uploading to Google Sheets..."):
                save_data(temp_df)
                st.success(f"Hole {hole_to_edit} data secured!")
                st.rerun()
