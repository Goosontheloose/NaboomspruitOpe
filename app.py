import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.title("Connection Handshake Test")

try:
    # 1. Check Secrets
    st.write("Checking Secrets...")
    s = st.secrets["connections"]["gsheets"]
    
    # 2. Authenticate
    st.write("Authenticating with Google...")
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(s, scopes=scopes)
    client = gspread.authorize(creds)
    
    # 3. Open Sheet
    st.write("Opening Spreadsheet...")
    sheet_id = s["spreadsheet"]
    sh = client.open_by_key(sheet_id)
    worksheet = sh.get_worksheet(0)
    
    # 4. Attempt Write (The Handshake)
    if st.button("RUN HANDSHAKE"):
        worksheet.update_acell('A1', 'Handshake Successful')
        st.success("✅ SUCCESS: App can talk to Google Sheets!")
        st.balloons()

except Exception as e:
    st.error("❌ HANDSHAKE FAILED")
    st.exception(e)
