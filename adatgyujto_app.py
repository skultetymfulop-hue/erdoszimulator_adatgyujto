import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import random

# --- 1. KAPCSOLAT FÜGGVÉNY ---
def test_upload():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = { ... } # (az adataid maradnak)
        
        # Kulcs javítása
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # Módosított megnyitás:
        spreadsheet = client.open_by_url("https://docs.google.com/spreadsheets/d/10DyyNfaYh0C9orj-F_Go8Har46Tsm1JNISzecQ1dcIc/edit")
        sheet = spreadsheet.get_worksheet(0)
        
        # Adatok küldése string-ként (ez a legbiztosabb a 400-as hiba ellen)
        data = [str(random.randint(1,100)), str(random.randint(1,100)), str(random.randint(1,100))]
        
        sheet.append_row(data, value_input_option='RAW')
        return "Siker!"
    except Exception as e:
        return f"Hiba: {str(e)}"
