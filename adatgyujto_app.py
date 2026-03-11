import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def simple_test():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Most már benne van a private_key_id is!
        creds_dict = {
            "type": "service_account",
            "project_id": "genial-acronym-489918-a6",
            "private_key_id": "85c43711722d4586bfaca301bf5e186b41d923f1",
            "private_key": """-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDpIW15OnV0ZZKV\nlE5jPM5QQL0malqFnK3RjQ4V0N/wTZFw3sJ4oXybXY266xZ3bEbiCjiAy57Kuzhk\nbU5gHuLM3+PBsO99wCDLJSe1QwV90E0hqWeHuTksaSy68FwoBbiAk9jB7SR3Ormq\nbXQnzCLpwaU5Fs2x/Paq7WSEGU7PR+wklXukO5yCXhcIwh/4//fkWbVmYght7k2h\nCnXPOoyXNEPGvbDtc01u26C6jZCw9b3iKZpGadkYUfyQxEEX6TXn0ExrqYg5AOpG\nb9YeNdeQMtkEC6rMP1kbRwYEBoJLmATHfbIrm2ig1dMPJPuvA9EhEuknzIFtuM1h\nfYX+cDxNAgMBAAECggEAEDzmj+DRQQX5H4eIrTNVSHQ16IjUXMWUusmJH15g1q9E\nb9joMThIQlcSEeChfDhzuHdPR7NHEGZZb29Im/vSvsPibIGLMNZSwmuIWED+jyyU\nzsEqp6KwV4ZM2gl3VcdOOlBx8tH2bgKOX49HnaUDkoYNIMyUj67nrHCkBWpw2ZGO\nGXZjpZ4gWPOgWwS9B9vJpo7YoQo94TJ54wV346aF/QAKZvgOB9xjWK/oFiipTUIN\niSUvjuq5td50A/oofvYki7sdX4uN1CiCN9rlSpz41LJ9xr2RAWkuWhwDGnH0cP8Y\nFn2+oWPtH66AdHs8cUl4PVdbehUZ3cLZth+0vD6JqQKBgQD3fTZJDAB48dPMeyIO\nl4GacMQ2svAh1u3ECEpx+WUZxCArS6nRus3+58b2i3A/Sd6rS4rrP6eMXsYz5/DA\nSqtIsOISfrvy5oT1k/NloMGAoTnLKKbnOpoE+sCTV0z14LS91K7kt+ZUaZaHlJyx\nab1J+d/5LHFf2Vw2KD5rdXYFWQKBgQDxJc8ouU3Uhtp/y34NK1QihJ54uHi0hrC6\naohb0jitf7mgfjFNBmbR4Z/0+spKd5KFQDL+tovAvS6jYgbq8a/4BHY7ruCiq/xu\ntgp5A5ZwxxvMYeML8aXKYzbXfAAXiA/71gFPwDMtq8OyVXcs5Xp8ghacu0rCFGmh\nnT7GajqsFQKBgHijdnTA/vH1n3KLixxlye1IjrzDGL7GD/yAthk8ooWezreMGGl9\nj7Bzts6zRbH0BjClkEAANWH9SMxAgWCahUfXwTuWv3M13xX+WqTtaaWT8aIQXNtV\n+4H14S1xXrh0ImZuaBphcksvdQr97CunCXgn7398pH8+au6TS2oCRddxAoGAbLha\nJIce4uGFozYwd2mAfiuCcvTgXquXBATBw3wM15QNMaGTQqHPO3LYtg9Xoqk0IuVl\n2FaevV/NphWs/sHGTzBbyd63IkAeCCAEqriGXAQ4sTW0so7Y6109vXsHY5SReD3s\ny3Lg4AdfrIhBubkgNwBDh5gdRVEEqruFMNl16F0CgYEAsMCuMflQvpCI9dBWEs2T\n/ZDkjDX9RQua6WptYJkNB6KgJGJliA+G7P6jVVf5l/E1ej4Qz1vlhbY1rFBWCNKo\njYVz1mcYvehrgVY1B2EJqP+Mp3UtLBp9rn7rhljLow8pZwc472PrufUtygcTs9hn\nzRNV/oST+dvRz7wXRgM5zt8=\n-----END PRIVATE KEY-----\n""",
            "client_email": "erdo-mentes@genial-acronym-489918-a6.iam.gserviceaccount.com"
        }
        
        # Kulcs javítása
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        # Hitelesítés
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # Táblázat megnyitása
        sheet = client.open_by_key("10DyyNfaYh0C9orj-F_Go8Har46Tsm1JNISzecQ1dcIc").get_worksheet(0)
        
        # 1-től 10-ig számok
        szamok = [list(range(1, 11))]
        
        # Írás az első sorba
        sheet.update('A1:J1', szamok)
        
        return "✅ SIKER! Az első sorban ott kell lennie a számoknak 1-10-ig."

    except Exception as e:
        return f"❌ Hiba: {str(e)}"

# --- UI ---
st.title("🧪 Szuper-egyszerű teszt v2")
if st.button("Írj 1-10-ig az első sorba!"):
    st.write(simple_test())
