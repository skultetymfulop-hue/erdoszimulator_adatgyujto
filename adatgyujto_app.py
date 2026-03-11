import streamlit as st
from google.oauth2.service_account import Credentials
import gspread

# 1. Beolvasás
creds_dict = dict(st.secrets["gcp_service_account"])

# 2. Kulcs tisztítása (ha mégis maradt benne manuális \n)
creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

# 3. Kapcsolódás
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
gc = gspread.authorize(creds)

# Teszteljük le egy létező táblázattal
try:
    # Itt a saját táblázatod ID-ját használd (az URL-ből a d/ utáni rész)
    sh = gc.open_by_key("10DyyNfaYh0C9orj-F_Go8Har46Tsm1JNISzecQ1dcIc")
    st.success("Sikerült! A táblázat elérhető.")
except Exception as e:
    st.error(f"A kulcs már jó, de a táblázatot nem érem el: {e}")
