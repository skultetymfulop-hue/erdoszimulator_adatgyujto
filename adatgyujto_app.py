import streamlit as st
from google.oauth2.service_account import Credentials
import gspread

# A Secrets-ből olvassuk ki a szótárat
creds_dict = st.secrets["gcp_service_account"]

scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

# Most már próbálhatod nyitni a táblázatot
spreadsheet_url = "https://docs.google.com/spreadsheets/d/10DyyNfaYh0C9orj-F_Go8Har46Tsm1JNISzecQ1dcIc/edit"
sheet = client.open_by_url(spreadsheet_url).sheet1

st.success("Sikerült csatlakozni!")
