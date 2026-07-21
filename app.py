import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os
import traceback

# --- APP CONFIG ---
st.set_page_config(page_title="Naboom Nuut: Tactical Open", layout="wide")

# --- CSS STYLING ---
st.markdown("""
    <style>
    .centered-header { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding-bottom: 20px; }
    .main-title { color: #BFFF00; margin-top: 10px; font-size: 2.5rem; font-weight: bold; }
    .stroke-badge { background-color: #333; color: #BFFF00; padding: 2px 10px; border-radius: 12px; font-size: 0.85rem; margin-left: 10px; border: 1px solid #444; }
    </style>
    """, unsafe_allow_html=True)

# --- CONSTANTS ---
logo_path = "Naboom logo Nuut.png"
players = ["Bennie", "Adriaan", "Danie", "Martin", "Frederik"]
hcp_map = {"Bennie": 36, "Adriaan": 33, "Danie": 33, "Martin": 32, "Frederik": 32}
course_par = [4](https://github.com/burnash/gspread/issues/1310 "inline-citation")[4](https://github.com/burnash/gspread/issues/1310 "inline-citation")[5](https://docs.gspread.org/en/v6.0.0/user-guide.html "inline-citation")[3](https://docs.gspread.org/en/v6.0.0/ "inline-citation")[5](https://docs.gspread.org/en/v6.0.0/user-guide.html "inline-citation")[4](https://github.com/burnash/gspread/issues/1310 "inline-citation")[4](https://github.com/burnash/gspread/issues/1310 "inline-citation")[3](https://docs.gspread.org/en/v6.0.0/ "inline-citation")[4](https://github.com/burnash/gspread/issues/1310 "inline-citation")[4](https://github.com/burnash/gspread/issues/1310 "inline-citation")[4](https://github.com/burnash/gspread/issues/1310 "inline-citation")[5](https://docs.gspread.org/en/v6.0.0/user-guide.html "inline-citation")[3](https://docs.gspread.org/en/v6.0.0/ "inline-citation")[5](https://docs.gspread.org/en/v6.0.0/user-guide.html "inline-citation")[4](https://github.com/burnash/gspread/issues/1310 "inline-citation")[4](https://github.com/burnash/gspread/issues/1310 "inline-citation")[3](https://docs.gspread.org/en/v6.0.0/ "inline-citation")[4](https://github.com/burnash/gspread/issues/1310 "inline-citation")
course_idx = [17][3](https://docs.gspread.org/en/v6.0.0/ "inline-citation")[7][5](https://docs.gspread.org/en/v6.0.0/user-guide.html "inline-citation")[9][13][1](https://stackoverflow.com/questions/72270126/how-to-update-a-row-using-the-gspread-python-module "inline-citation")[15][11][14][6][8][18][10][2](https://pypi.org/project/gspread/ "inline-citation")[4](https://github.com/burnash/gspread/issues/1310 "inline-citation")[16][12]
headers = ["Player", "Hole", "Score", "Drinks", "Camo", "Throw", "Kick", "Mully"]

# --- DATABASE CONNECTION ---
@st.cache_resource
def get_gspread_client():
    s = st.secrets["connections"]["gsheets"]
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(s, scopes=scopes)
    return gspread.authorize(creds)

def load_data():
    client = get_gspread_client()
    sheet_id = st.secrets["connections"]["gsheets"]["spreadsheet"]
    sh = client.open_by_key(sheet_id)
    worksheet = sh.get_worksheet(0)
    data = worksheet.get_all_records()
    if not data:
        return pd.DataFrame(columns=headers)
    return pd.DataFrame(data)

def save_data(df):
    client = get_gspread_client()
    sheet_id = st.secrets["connections"]["gsheets"]["spreadsheet"]
    sh = client.open_by_key(sheet_id)
    worksheet = sh.get_worksheet(0)
    worksheet.clear()
    # Convert all to string for safety, and use named arguments for version compatibility
    df_filled = df.fillna(0).astype(str)
    vals = [df_filled.columns.values.tolist()] + df_filled.values.tolist()
    worksheet.update(values=vals, range_name="A1")
    st.cache_data.clear()

# --- HELPER FUNCTIONS ---
def get_allowed_strokes(player, hole_num):
    hcp = hcp_map.get(player, 0)
    idx = course_idx[hole_num - 1]
    return (hcp // 18) + (1 if idx <= (hcp % 18) else 0)

def get_points(row):
    try:
        score = int(row['Score'])
        if score == 0: return 0
        h_idx = int(row['Hole']) - 1
        par = course_par[h_idx]
        strokes = get_allowed_strokes(row['Player'], int(row['Hole']))
        net = score - strokes
        pts = max(0, 2 - (net - par))
        return pts * 2 if str(row['Camo']).lower() == "true" else pts
    except:
        return 0

# --- DATA INITIALIZATION ---
try:
    df = load_data()
    if df.empty: raise ValueError
except Exception:
    rows = []
    for p in players:
        for h in range(1, 19):
            rows.append({"Player": p, "Hole": h, "Score": 0, "Drinks": 0, "Camo": False, "Throw": False, "Kick": False, "Mully": 0})
    df = pd.DataFrame(rows)

# --- UI HEADER ---
st.markdown('<div class="centered-header">', unsafe_allow_html=True)
if os.path.exists(logo_path):
    st.image(logo_path, width=180)
st.markdown('<p class="main-title">NABOOM NUUT: TACTICAL OPEN</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🏆 LEADERBOARD", "🎒 THE ARSENAL", "🎯 HOLE COMMAND"])

with tab1:
    df['Points'] = df.apply(get_points, axis=1)
    df['Score'] = pd.to_numeric(df['Score'], errors='coerce').fillna(0)
    df['Drinks'] = pd.to_numeric(df['Drinks'], errors='coerce').fillna(0)
    summary = df.groupby("Player").agg({'Points': 'sum', 'Score': 'sum', 'Drinks': 'sum'}).reset_index()
    summary['Gimme (cm)'] = summary['Drinks'] * 10
    st.dataframe(summary.sort_values("Points", ascending=False), use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Tactical Resource Inventory")
    arsenal = []
    for p in players:
        p_data = df[df['Player'] == p]
        arsenal.append({
            "Player": p,
            "Camo Used": (p_data['Camo'].astype(str).str.lower() == "true").sum(),
            "Throws/Kicks": ((p_data['Throw'].astype(str).str.lower() == "true").sum() + (p_data['Kick'].astype(str).str.lower() == "true").sum()),
            "Mullies Used": pd.to_numeric(p_data['Mully'], errors='coerce').sum()
        })
    st.table(pd.DataFrame(arsenal))
    
    st.divider()
    if st.button("🚨 RESET & INITIALIZE GOOGLE SHEET", type="primary", use_container_width=True):
        try:
            save_data(df)
            st.success("Google Sheet has been formatted and connected successfully!")
            st.rerun()
        except Exception as e:
            st.error("Setup Failed. See technical details below:")
            st.exception(e)

with tab3:
    hole_to_edit = st.selectbox("Select Hole", range(1, 19))
    h_idx = hole_to_edit - 1
    st.markdown(f"### Hole {hole_to_edit} (Par {course_par[h_idx]} | Index {course_idx[h_idx]})")
    
    with st.form("score_entry_form"):
        temp_df = df.copy()
        for p in players:
            p_mask = (temp_df['Player'] == p) & (temp_df['Hole'].astype(int) == hole_to_edit)
            idx = temp_df[p_mask].index[0]
            strokes = get_allowed_strokes(p, hole_to_edit)
            st.markdown(f"**{p}** <span class='stroke-badge'>Hole Strokes: {strokes}</span>", unsafe_allow_html=True)
            
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            temp_df.at[idx, 'Score'] = c1.number_input("Score", 0, 15, value=int(df.at[idx, 'Score']), key=f"s_{p}_{hole_to_edit}")
            temp_df.at[idx, 'Drinks'] = c2.number_input("Drinks", 0, 10, value=int(df.at[idx, 'Drinks']), key=f"d_{p}_{hole_to_edit}")
            temp_df.at[idx, 'Camo'] = c3.checkbox("Camo", value=(str(df.at[idx, 'Camo']).lower() == "true"), key=f"c_{p}_{hole_to_edit}")
            temp_df.at[idx, 'Throw'] = c4.checkbox("Throw", value=(str(df.at[idx, 'Throw']).lower() == "true"), key=f"t_{p}_{hole_to_edit}")
            temp_df.at[idx, 'Kick'] = c5.checkbox("Kick", value=(str(df.at[idx, 'Kick']).lower() == "true"), key=f"k_{p}_{hole_to_edit}")
            temp_df.at[idx, 'Mully'] = c6.number_input("Mully", 0, 2, value=int(df.at[idx, 'Mully']), key=f"m_{p}_{hole_to_edit}")
            st.divider()

        if st.form_submit_button("💾 SYNC SCORES TO CLOUD", use_container_width=True):
            try:
                save_data(temp_df)
                st.success("Synced!")
                st.rerun()
            except Exception as e:
                st.error("Sync Failed!")
                st.exception(e) # This will show the REAL error on screen
