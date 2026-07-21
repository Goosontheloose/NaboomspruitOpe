import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os

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
course_par = [4, 4, 5, 3, 5, 4, 4, 3, 4, 4, 4, 5, 3, 5, 4, 4, 3, 4]
course_idx = [17, 3, 7, 5, 9, 13, 1, 15, 11, 14, 6, 8, 18, 10, 2, 4, 16, 12]

# --- DATABASE CONNECTION ---
def get_worksheet():
    s = st.secrets["connections"]["gsheets"]
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(s, scopes=scopes)
    client = gspread.authorize(creds)
    sheet_id = s["spreadsheet"].strip()
    return client.open_by_key(sheet_id).get_worksheet(0)

def load_data():
    ws = get_worksheet()
    data = ws.get_all_records()
    return pd.DataFrame(data)

def save_hole_data(hole_num, hole_rows_df):
    """Updates ONLY the rows corresponding to the specific hole."""
    ws = get_worksheet()
    all_data = ws.get_all_records()
    full_df = pd.DataFrame(all_data)
    
    # Update only the matching hole indices
    for _, new_row in hole_rows_df.iterrows():
        mask = (full_df['Player'] == new_row['Player']) & (full_df['Hole'] == hole_num)
        if mask.any():
            idx = full_df.index[mask][0]
            # gspread is 1-indexed, +2 because of header and 0-indexing
            row_to_update = int(idx) + 2 
            
            # Prepare update list: Score(3), Drinks(4), Camo(5), Throw(6), Kick(7), Mully(8)
            updates = [
                new_row['Score'], new_row['Drinks'], 
                str(new_row['Camo']).upper(), str(new_row['Throw']).upper(), 
                str(new_row['Kick']).upper(), new_row['Mully']
            ]
            ws.update(range_name=f"C{row_to_update}:H{row_to_update}", values=[updates])

# --- SCORING LOGIC ---
def get_allowed_strokes(player, hole_num):
    hcp = hcp_map.get(player, 0)
    idx = course_idx[hole_num - 1]
    return (hcp // 18) + (1 if idx <= (hcp % 18) else 0)

def get_points(row):
    try:
        score = int(row['Score'])
        if score <= 0: return 0
        h_idx = int(row['Hole']) - 1
        net = score - get_allowed_strokes(row['Player'], int(row['Hole']))
        pts = max(0, 2 - (net - course_par[h_idx]))
        return pts * 2 if str(row['Camo']).upper() == "TRUE" else pts
    except: return 0

# --- MAIN APP ---
st.markdown('<div class="centered-header">', unsafe_allow_html=True)
if os.path.exists(logo_path): st.image(logo_path, width=150)
st.markdown('<p class="main-title">NABOOM NUUT: TACTICAL OPEN</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

try:
    df = load_data()
    tab1, tab2, tab3 = st.tabs(["🏆 LEADERBOARD", "🎒 THE ARSENAL", "🎯 HOLE COMMAND"])

    with tab1:
        df['Points'] = df.apply(get_points, axis=1)
        summary = df.groupby("Player").agg({'Points': 'sum', 'Score': 'sum', 'Drinks': 'sum'}).reset_index()
        summary['Gimme (cm)'] = summary['Drinks'] * 10
        st.dataframe(summary.sort_values("Points", ascending=False), use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Tactical Resource Inventory")
        res = []
        for p in players:
            p_df = df[df['Player'] == p]
            res.append({
                "Player": p,
                "Camo": (p_df['Camo'].astype(str).str.upper() == "TRUE").sum(),
                "T/K": (p_df['Throw'].astype(str).str.upper() == "TRUE").sum() + (p_df['Kick'].astype(str).str.upper() == "TRUE").sum(),
                "Mullies": p_df['Mully'].sum()
            })
        st.table(pd.DataFrame(res))

    with tab3:
        h_select = st.selectbox("Select Hole", range(1, 19))
        h_df = df[df['Hole'] == h_select].copy()
        
        with st.form("hole_form"):
            for i, row in h_df.iterrows():
                p = row['Player']
                st.markdown(f"**{p}** <span class='stroke-badge'>Strokes: {get_allowed_strokes(p, h_select)}</span>", unsafe_allow_html=True)
                c1, c2, c3, c4, c5, c6 = st.columns(6)
                h_df.at[i, 'Score'] = c1.number_input("Score", 0, 15, value=int(row['Score']), key=f"s{p}")
                h_df.at[i, 'Drinks'] = c2.number_input("Drinks", 0, 10, value=int(row['Drinks']), key=f"d{p}")
                h_df.at[i, 'Camo'] = c3.checkbox("Camo", value=(str(row['Camo']).upper() == "TRUE"), key=f"c{p}")
                h_df.at[i, 'Throw'] = c4.checkbox("Throw", value=(str(row['Throw']).upper() == "TRUE"), key=f"t{p}")
                h_df.at[i, 'Kick'] = c5.checkbox("Kick", value=(str(row['Kick']).upper() == "TRUE"), key=f"k{p}")
                h_df.at[i, 'Mully'] = c6.number_input("Mully", 0, 2, value=int(row['Mully']), key=f"m{p}")
            
            if st.form_submit_button("💾 SYNC HOLE SCORES"):
                save_hole_data(h_select, h_df)
                st.success(f"Hole {h_select} Synced!")
                st.rerun()

except Exception as e:
    st.error("Connection Error")
    st.exception(e)
