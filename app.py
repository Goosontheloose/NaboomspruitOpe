import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os

# --- APP CONFIG ---
st.set_page_config(page_title="Naboom Nuut: Tactical Open", layout="wide")

# --- CUSTOM CSS FOR THE TACTICAL SCORECARD ---
st.markdown("""
    <style>
    .centered-header { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding-bottom: 20px; }
    .main-title { color: #BFFF00; margin-top: 10px; font-size: 2.5rem; font-weight: bold; }
    .stroke-badge { background-color: #333; color: #BFFF00; padding: 2px 10px; border-radius: 12px; font-size: 0.85rem; margin-left: 10px; border: 1px solid #444; }
    
    /* Scorecard Table Styling */
    .sc-table { width: 100%; border-collapse: collapse; background-color: #111; color: white; font-family: sans-serif; font-size: 0.9rem; }
    .sc-table th, .sc-table td { border: 1px solid #333; padding: 8px; text-align: center; }
    .sc-table th { background-color: #222; color: #BFFF00; }
    .player-name { text-align: left !important; font-weight: bold; min-width: 120px; }
    
    /* Powerup Indicators */
    .camo-active { background-color: #4C6400 !important; color: #BFFF00 !important; font-weight: bold; border: 2px solid #BFFF00 !important; }
    .power-icon { font-size: 0.7rem; display: block; margin-top: 2px; }
    .throw-tag { color: #FF7A00; }
    .kick-tag { color: #FF4B4B; }
    .mully-tag { color: #A06BFF; }
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
    try:
        s = st.secrets["connections"]["gsheets"]
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(s, scopes=scopes)
        client = gspread.authorize(creds)
        sheet_id = s["spreadsheet"].strip()
        return client.open_by_key(sheet_id).get_worksheet(0)
    except Exception as e:
        st.error(f"GSheets Connection Error: {e}")
        return None

def load_data():
    ws = get_worksheet()
    if ws:
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        for col in ['Camo', 'Throw', 'Kick']:
            df[col] = df[col].astype(str).str.upper()
        return df
    return pd.DataFrame()

def save_atomic_hole(hole_num, player_updates):
    ws = get_worksheet()
    if not ws: return
    # Atomic math: Header(1) + (Hole-1)*5players + 1
    start_row = ((hole_num - 1) * len(players)) + 2
    batch_values = []
    for p in players:
        data = player_updates[p]
        batch_values.append([
            str(data['Score']), str(data['Drinks']), 
            str(data['Camo']).upper(), str(data['Throw']).upper(), 
            str(data['Kick']).upper(), str(data['Mully'])
        ])
    ws.update(range_name=f"C{start_row}:H{start_row+4}", values=batch_values)

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

# --- UI HEADER ---
st.markdown('<div class="centered-header">', unsafe_allow_html=True)
if os.path.exists(logo_path): st.image(logo_path, width=150)
st.markdown('<p class="main-title">NABOOM NUUT: TACTICAL OPEN</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

df = load_data()

if not df.empty:
    tab1, tab2, tab3 = st.tabs(["🏆 LIVE SCORECARD", "🎒 THE ARSENAL", "🎯 HOLE COMMAND"])

    with tab1:
        # Build HTML Scorecard
        df['Points'] = df.apply(get_points, axis=1)
        
        html = '<table class="sc-table"><tr><th>PLAYER</th>'
        for h in range(1, 19): html += f'<th>{h}</th>'
        html += '<th>TOT</th><th>PTS</th></tr>'
        
        for p in players:
            p_data = df[df['Player'] == p].sort_values('Hole')
            total_score = p_data['Score'].astype(int).sum()
            total_pts = p_data['Points'].sum()
            
            html += f'<tr><td class="player-name">{p}</td>'
            for _, row in p_data.iterrows():
                # Classes and Icons
                is_camo = str(row['Camo']).upper() == "TRUE"
                cell_class = 'camo-active' if is_camo else ''
                
                icons = ""
                if str(row['Throw']).upper() == "TRUE": icons += '<span class="power-icon throw-tag">T</span>'
                if str(row['Kick']).upper() == "TRUE": icons += '<span class="power-icon kick-tag">K</span>'
                if int(row['Mully']) > 0: icons += f'<span class="power-icon mully-tag">M{row["Mully"]}</span>'
                
                html += f'<td class="{cell_class}">{row["Score"]}<br>{icons}</td>'
            
            html += f'<td style="background:#222">{total_score}</td>'
            html += f'<td style="background:#222; color:#BFFF00; font-weight:bold;">{total_pts}</td></tr>'
        
        html += '</table>'
        st.markdown(html, unsafe_allow_html=True)
        
        # Drinks/Gimme Section
        st.divider()
        drinks_df = df.groupby("Player")['Drinks'].sum().reset_index()
        drinks_df['Gimme (cm)'] = drinks_df['Drinks'] * 10
        st.dataframe(drinks_df.sort_values("Drinks", ascending=False), use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Tactical Resource Inventory")
        res = []
        for p in players:
            p_df = df[df['Player'] == p]
            res.append({
                "Player": p,
                "Camo Ball": "USED" if (p_df['Camo'] == "TRUE").any() else "Ready",
                "Throws/Kicks (Out)": (p_df[p_df['Hole'] <= 9]['Throw'] == "TRUE").sum() + (p_df[p_df['Hole'] <= 9]['Kick'] == "TRUE").sum(),
                "Throws/Kicks (In)": (p_df[p_df['Hole'] > 9]['Throw'] == "TRUE").sum() + (p_df[p_df['Hole'] > 9]['Kick'] == "TRUE").sum(),
                "Mulligans Used": pd.to_numeric(p_df['Mully']).sum()
            })
        st.table(pd.DataFrame(res))

    with tab3:
        h_select = st.selectbox("Select Hole to Update", range(1, 19))
        h_df = df[df['Hole'] == h_select]
        
        with st.form("surgical_hole_form"):
            updates = {}
            for p in players:
                p_row = h_df[h_df['Player'] == p].iloc[0]
                st.markdown(f"**{p}** <span class='stroke-badge'>Strokes: {get_allowed_strokes(p, h_select)}</span>", unsafe_allow_html=True)
                c1, c2, c3, c4, c5, c6 = st.columns(6)
                
                s = c1.number_input("Score", 0, 15, value=int(p_row['Score']), key=f"s{p}")
                d = c2.number_input("Drinks", 0, 10, value=int(p_row['Drinks']), key=f"d{p}")
                c = c3.checkbox("Camo", value=(str(p_row['Camo']).upper() == "TRUE"), key=f"c{p}")
                t = c4.checkbox("Throw", value=(str(p_row['Throw']).upper() == "TRUE"), key=f"t{p}")
                k = c5.checkbox("Kick", value=(str(p_row['Kick']).upper() == "TRUE"), key=f"k{p}")
                m = c6.number_input("Mully", 0, 2, value=int(p_row['Mully']), key=f"m{p}")
                
                updates[p] = {'Score': s, 'Drinks': d, 'Camo': c, 'Throw': t, 'Kick': k, 'Mully': m}
            
            if st.form_submit_button(f"🎯 SYNC HOLE {h_select} ONLY"):
                save_atomic_hole(h_select, updates)
                st.success(f"Atomic Sync for Hole {h_select} Complete!")
                st.rerun()
else:
    st.warning("Wait... Database connection failed or spreadsheet is empty.")
