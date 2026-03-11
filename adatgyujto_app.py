import streamlit as st
import gspread
import random
import json
from oauth2client.service_account import ServiceAccountCredentials

def test_upload():
    try:
        # 1. Definiáljuk a hatóköröket
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # 2. A teljes JSON tartalom, amit megadtál (ez a legbiztosabb módszer)
        # Figyelj: a private_key-ben a \n karakterek maradjanak meg a stringben!
        creds_info = {
            "type": "service_account",
            "project_id": "genial-acronym-489918-a6",
            "private_key_id": "85c43711722d4586bfaca301bf5e186b41d923f1",
            "private_key": """-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDpIW15OnV0ZZKV\nlE5jPM5QQL0malqFnK3RjQ4V0N/wTZFw3sJ4oXybXY266xZ3bEbiCjiAy57Kuzhk\nbU5gHuLM3+PBsO99wCDLJSe1QwV90E0hqWeHuTksaSy68FwoBbiAk9jB7SR3Ormq\nbXQnzCLpwaU5Fs2x/Paq7WSEGU7PR+wklXukO5yCXhcIwh/4//fkWbVmYght7k2h\nCnXPOoyXNEPGvbDtc01u26C6jZCw9b3iKZpGadkYUfyQxEEX6TXn0ExrqYg5AOpG\nb9YeNdeQMtkEC6rMP1kbRwYEBoJLmATHfbIrm2ig1dMPJPuvA9EhEuknzIFtuM1h\nfYX+cDxNAgMBAAECggEAEDzmj+DRQQX5H4eIrTNVSHQ16IjUXMWUusmJH15g1q9E\nb9joMThIQlcSEeChfDhzuHdPR7NHEGZZb29Im/vSvsPibIGLMNZSwmuIWED+jyyU\nzsEqp6KwV4ZM2gl3VcdOOlBx8tH2bgKOX49HnaUDkoYNIMyUj67nrHCkBWpw2ZGO\nGXZjpZ4gWPOgWwS9B9vJpo7YoQo94TJ54wV346aF/QAKZvgOB9xjWK/oFiipTUIN\niSUvjuq5td50A/oofvYki7sdX4uN1CiCN9rlSpz41LJ9xr2RAWkuWhwDGnH0cP8Y\nFn2+oWPtH66AdHs8cUl4PVdbehUZ3cLZth+0vD6JqQKBgQD3fTZJDAB48dPMeyIO\nl4GacMQ2svAh1u3ECEpx+WUZxCArS6nRus3+58b2i3A/Sd6rS4rrP6eMXsYz5/DA\nSqtIsOISfrvy5oT1k/NloMGAoTnLKKbnOpoE+sCTV0z14LS91K7kt+ZUaZaHlJyx\nab1J+d/5LHFf2Vw2KD5rdXYFWQKBgQDxJc8ouU3Uhtp/y34NK1QihJ54uHi0hrC6\naohb0jitf7mgfjFNBmbR4Z/0+spKd5KFQDL+tovAvS6jYgbq8a/4BHY7ruCiq/xu\ntgp5A5ZwxxvMYeML8aXKYzbXfAAXiA/71gFPwDMtq8OyVXcs5Xp8ghacu0rCFGmh\nnT7GajqsFQKBgHijdnTA/vH1n3KLixxlye1IjrzDGL7GD/yAthk8ooWezreMGGl9\nj7Bzts6zRbH0BjClkEAANWH9SMxAgWCahUfXwTuWv3M13xX+WqTtaaWT8aIQXNtV\n+4H14S1xXrh0ImZuaBphcksvdQr97CunCXgn7398pH8+au6TS2oCRddxAoGAbLha\nJIce4uGFozYwd2mAfiuCcvTgXquXBATBw3wM15QNMaGTQqHPO3LYtg9Xoqk0IuVl\n2FaevV/NphWs/sHGTzBbyd63IkAeCCAEqriGXAQ4sTW0so7Y6109vXsHY5SReD3s\ny3Lg4AdfrIhBubkgNwBDh5gdRVEEqruFMNl16F0CgYEAsMCuMflQvpCI9dBWEs2T\n/ZDkjDX9RQua6WptYJkNB6KgJGJliA+G7P6jVVf5l/E1ej4Qz1vlhbY1rFBWCNKo\njYVz1mcYvehrgVY1B2EJqP+Mp3UtLBp9rn7rhljLow8pZwc472PrufUtygcTs9hn\nzRNV/oST+dvRz7wXRgM5zt8=\n-----END PRIVATE KEY-----\n""",
            "client_email": "erdo-mentes@genial-acronym-489918-a6.iam.gserviceaccount.com",
            "client_id": "111987957484558081367",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/erdo-mentes%40genial-acronym-489918-a6.iam.gserviceaccount.com"
        }

        # 3. Hitelesítés javított kulccsal
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client = gspread.authorize(creds)
        
        # 4. Megnyitás és adatküldés
        # Csak az ID-t használjuk a megnyitáshoz, a sallang nélkül
        sheet_id = "10DyyNfaYh0C9orj-F_Go8Har46Tsm1JNISzecQ1dcIc"
        spreadsheet = client.open_by_key(sheet_id)
        sheet = spreadsheet.get_worksheet(0)
        
        # Adatok listája
        row = [random.randint(1,100), random.randint(1,100), random.randint(1,100)]
        
        # RAW opció a 400-as hiba elkerülésére
        sheet.append_row(row, value_input_option='USER_ENTERED')
        
        return f"Siker! Beküldve: {row}"
        
    except Exception as e:
        return f"Hiba: {str(e)}"

# --- UI ---
st.title("🧪 Végső Google Sheets Teszt")

if st.button("TESZT ADAT KÜLDÉSE"):
    with st.spinner("Csatlakozás..."):
        res = test_upload()
        st.write(res)
