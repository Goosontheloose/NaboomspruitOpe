import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os

# --- APP CONFIG ---
st.set_page_config(page_title="Naboom Nuut: Tactical Open", layout="wide")

# --- CSS FOR PERFECT CENTERING & STYLES ---
st.markdown("""
    <style>
    .centered-header {
        display: flex; flex-direction: column; align-items: center;
        justify-content: center; text-align: center; padding-bottom: 20px;
    }
    .main-title { color: #BFFF00; margin-top: 10px; font-size: 2.5rem; font-weight: bold; }
    .sub-title { color: #888; font-size: 1rem; margin-top: -10px; }
    .stroke-badge {
        background-color: #333; color: #BFFF00; padding: 2px 10px;
        border-radius: 12px; font-size: 0.85rem; margin-left: 10px; border: 1px solid #444;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGO HANDLING ---
logo_path = "Naboom logo Nuut.png"

# --- DATABASE CONNECTION ---
@st.cache_resource
def get_gspread_client():
    s = st.secrets["connections"]["gsheets"]
    # We MUST have both Sheet and Drive scopes
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(s, scopes=scopes)
    return gspread.authorize(creds)

def load_data():
    client = get_gspread_client()
    # Try opening by URL or Key
    url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    sh = client.open_by_url(url)
    worksheet = sh.get_worksheet(0)
    return pd.DataFrame(worksheet.get_all_records())

def save_data(df):
    client = get_gspread_client()
    url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    sh = client.open_by_url(url)
    worksheet = sh.get_worksheet(0)
    worksheet.clear()
    # Ensure no NaN values go to Google
    df_filled = df.fillna(0).astype(str) 
    worksheet.update([df_filled.columns.values.tolist()] + df_filled.values.tolist())
    st.cache_data.clear()

# --- CONSTANTS ---
players = ["Bennie", "Adriaan", "Danie", "Martin", "Frederik"]
hcp_map = {"Bennie": 36, "Adriaan": 33, "Danie": 33, "Martin": 32, "Frederik": 32}
course_par = [4](https://community.latenode.com/t/using-gspread-to-connect-with-google-sheets/12551 "inline-citation")[4](https://community.latenode.com/t/using-gspread-to-connect-with-google-sheets/12551 "inline-citation")[5](https://stackoverflow.com/questions/39881518/permissions-error-when-running-a-script-in-a-google-spreadsheet "inline-citation")[3](https://stackoverflow.com/questions/53715582/google-sheets-api-permission-error-for-writing-with-gspread "inline-citation")[5](https://stackoverflow.com/questions/39881518/permissions-error-when-running-a-script-in-a-google-spreadsheet "inline-citation")[4](https://community.latenode.com/t/using-gspread-to-connect-with-google-sheets/12551 "inline-citation")[4](https://community.latenode.com/t/using-gspread-to-connect-with-google-sheets/12551 "inline-citation")[3](https://stackoverflow.com/questions/53715582/google-sheets-api-permission-error-for-writing-with-gspread "inline-citation")[4](https://community.latenode.com/t/using-gspread-to-connect-with-google-sheets/12551 "inline-citation")[4](https://community.latenode.com/t/using-gspread-to-connect-with-google-sheets/12551 "inline-citation")[4](https://community.latenode.com/t/using-gspread-to-connect-with-google-sheets/12551 "inline-citation")[5](https://stackoverflow.com/questions/39881518/permissions-error-when-running-a-script-in-a-google-spreadsheet "inline-citation")[3](https://stackoverflow.com/questions/53715582/google-sheets-api-permission-error-for-writing-with-gspread "inline-citation")[5](https://stackoverflow.com/questions/39881518/permissions-error-when-running-a-script-in-a-google-spreadsheet "inline-citation")[4](https://community.latenode.com/t/using-gspread-to-connect-with-google-sheets/12551 "inline-citation")[4](https://community.latenode.com/t/using-gspread-to-connect-with-google-sheets/12551 "inline-citation")[3](https://stackoverflow.com/questions/53715582/google-sheets-api-permission-error-for-writing-with-gspread "inline-citation")[4](https://community.latenode.com/t/using-gspread-to-connect-with-google-sheets/12551 "inline-citation")
course_idx = [17][3](https://stackoverflow.com/questions/53715582/google-sheets-api-permission-error-for-writing-with-gspread "inline-citation")[7][5](https://stackoverflow.com/questions/39881518/permissions-error-when-running-a-script-in-a-google-spreadsheet "inline-citation")[9][13][1](https://docs.gspread.org/en/v6.2.1/oauth2.html "inline-citation")[15][11][14][6][8][18][10][2](https://docs.gspread.org/_/downloads/en/v5.4.0/pdf/ "inline-citation")[4](https://community.latenode.com/t/using-gspread-to-connect-with-google-sheets/12551 "inline-citation")[16][12]

# --- LOAD DATA (With Safe Error Handling) ---
try:
    df = load_data()
except Exception:
    rows = []
    for p in players:
        for h in range(1, 19):
            rows.append({"Player": p, "Hole": h, "Score": 0, "Drinks": 0, "Camo": False, "Throw": False, "Kick": False, "Mully": 0})
    df = pd.DataFrame(rows)

# --- HELPER: GET STROKES ---
def get_allowed_strokes(player, hole_num):
    hcp = hcp_map.get(player, 0)
    idx = course_idx[hole_num - 1]
    return (hcp // 18) + (1 if idx <= (hcp % 18) else 0)

def get_points(row):
    if int(row['Score']) == 0: return 0
    h_idx = int(row['Hole']) - 1
    par = course_par[h_idx]
    strokes = get_allowed_strokes(row['Player'], int(row['Hole']))
    net = int(row['Score']) - strokes
    pts = max(0, 2 - (net - par))
    return pts * 2 if row['Camo'] in [True, "True", 1] else pts

# --- UI HEADER (CENTERED) ---
st.markdown('<div class="centered-header">', unsafe_allow_html=True)
if os.path.exists(logo_path):
    st.image(logo_path, width=200)
st.markdown('<p class="main-title">NABOOM NUUT: TACTICAL OPEN</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Sole Scorekeeper Portal | Tactical Resource Management</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

st.divider()

tab1, tab2, tab3 = st.tabs(["🏆 LEADERBOARD", "🎒 THE ARSENAL", "🎯 HOLE COMMAND"])

with tab1:
    df['Points'] = df.apply(get_points, axis=1)
    # Ensure numeric for math
    df['Score'] = pd.to_numeric(df['Score'])
    df['Drinks'] = pd.to_numeric(df['Drinks'])
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
            "Camo Used": (p_data['Camo'].astype(str) == "True").sum(),
            "Throws (1-9)": (p_data[p_data['Hole'].astype(int) <= 9]['Throw'].astype(str) == "True").sum(),
            "Throws (10-18)": (p_data[p_data['Hole'].astype(int) > 9]['Throw'].astype(str) == "True").sum(),
            "Mullies": pd.to_numeric(p_data['Mully']).sum()
        })
    st.table(pd.DataFrame(arsenal))

with tab3:
    hole_to_edit = st.selectbox("Select Hole", range(1, 19))
    h_idx = hole_to_edit - 1
    st.markdown(f"### Hole {hole_to_edit} (Par {course_par[h_idx]} | Index {course_idx[h_idx]})")
    
    with st.form("score_entry_form"):
        temp_df = df.copy()
        for p in players:
            idx = temp_df[(temp_df['Player'] == p) & (temp_df['Hole'].astype(int) == hole_to_edit)].index[0]
            strokes = get_allowed_strokes(p, hole_to_edit)
            st.markdown(f"**{p}** <span class='stroke-badge'>Hole Strokes: {strokes}</span>", unsafe_allow_html=True)
            
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            temp_df.at[idx, 'Score'] = c1.number_input("Score", 0, 15, value=int(df.at[idx, 'Score']), key=f"s_{p}_{hole_to_edit}")
            temp_df.at[idx, 'Drinks'] = c2.number_input("Drinks", 0, 10, value=int(df.at[idx, 'Drinks']), key=f"d_{p}_{hole_to_edit}")
            temp_df.at[idx, 'Camo'] = c3.checkbox("Camo", value=(str(df.at[idx, 'Camo']) == "True"), key=f"c_{p}_{hole_to_edit}")
            temp_df.at[idx, 'Throw'] = c4.checkbox("Throw", value=(str(df.at[idx, 'Throw']) == "True"), key=f"t_{p}_{hole_to_edit}")
            temp_df.at[idx, 'Kick'] = c5.checkbox("Kick", value=(str(df.at[idx, 'Kick']) == "True"), key=f"k_{p}_{hole_to_edit}")
            temp_df.at[idx, 'Mully'] = c6.number_input("Mully", 0, 2, value=int(df.at[idx, 'Mully']), key=f"m_{p}_{hole_to_edit}")
            st.divider()

        if st.form_submit_button("💾 SYNC SCORES TO CLOUD", use_container_width=True):
            save_data(temp_df)
            st.success(f"Hole {hole_to_edit} data secured!")
            st.rerun()

# --- DIAGNOSTIC TOOL (EXPANDER) ---
with st.expander("🛠 SYSTEM DIAGNOSTICS (Open this if Sync fails)"):
    try:
        client_email = st.secrets["connections"]["gsheets"]["client_email"]
        st.write(f"**1. Service Account Email:** `{client_email}`")
        st.info("Make sure the Google Sheet is shared with THIS EXACT email as an 'Editor'.")
        
        # Test Drive Access
        client = get_gspread_client()
        st.write("**2. API Connection:** ✅ Authenticated with Google")
        
        # Test File Access
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        sh = client.open_by_url(url)
        st.write(f"**3. Spreadsheet Found:** ✅ '{sh.title}'")
        st.success("System is fully operational. If you see an error above, check the Drive API.")
    except Exception as e:
        st.error(f"Diagnostic Failed: {e}")
        st.warning("If Step 3 failed but Step 1 is shared, you MUST enable the 'Google Drive API' in your Cloud Console.")
