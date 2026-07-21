import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.title("🔍 Deep Scout Diagnostic")

try:
    s = st.secrets["connections"]["gsheets"]
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(s, scopes=scopes)
    client = gspread.authorize(creds)

    # 1. VERIFY IDENTITY
    st.subheader("1. Identity Check")
    st.write(f"The App is logged in as: `{s['client_email']}`")
    st.info("Ensure this EXACT email is the one you shared the sheet with.")

    # 2. LIST ACCESSIBLE FILES
    st.subheader("2. Visibility Check")
    st.write("Searching for all files this account can see...")
    all_files = client.list_spreadsheet_files()
    
    if not all_files:
        st.warning("⚠️ THE ACCOUNT SEES ZERO FILES. This means the 'Share' step likely didn't save or there is a typo in the email address.")
    else:
        st.success(f"The account can see {len(all_files)} file(s):")
        for f in all_files:
            st.code(f"Name: {f['name']} | ID: {f['id']}")

    # 3. VERIFY SPECIFIC ID
    st.subheader("3. Targeting Check")
    target_id = s["spreadsheet"]
    st.write(f"Attempting to open specific ID: `{target_id}`")
    
    try:
        sh = client.open_by_key(target_id)
        st.balloons()
        st.success("✅ CONNECTION ESTABLISHED! You are ready to go.")
    except Exception as e:
        st.error("❌ TARGET BLOCKED")
        st.write("If you see the file in the list above but this step fails, you likely haven't enabled the **GOOGLE SHEETS API** (separate from the Drive API).")
        st.exception(e)

except Exception as e:
    st.error("CRITICAL CONFIG ERROR")
    st.exception(e)
