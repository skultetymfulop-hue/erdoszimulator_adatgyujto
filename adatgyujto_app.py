import gspread
from google.oauth2.service_account import Credentials

# 1. Beállítások - Másold ide a JSON fájlod tartalmát vagy az útvonalát
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info({
    "type": "service_account",
    "project_id": "genial-acronym-489918-a6",
    "private_key_id": "85c43711722d4586bfaca301bf5e186b41d923f1",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDpIW15OnV0ZZKV\n...", # Ide a teljes kulcs kell
    "client_email": "erdo-mentes@genial-acronym-489918-a6.iam.gserviceaccount.com",
    "token_uri": "https://oauth2.googleapis.com/token",
}, scopes=scope)

client = gspread.authorize(creds)

# 2. Tesztelés
spreadsheet_id = "10DyyNfaYh0C9orj-F_Go8Har46Tsm1JNISzecQ1dcIc"

try:
    sheet = client.open_by_key(spreadsheet_id).sheet1
    data = sheet.get_all_records()
    print("✅ SIKER! A kapcsolat él.")
    print(f"Az első sor adatai: {data[0] if data else 'Üres a táblázat'}")
except Exception as e:
    print("❌ HIBA történt:")
    print(e)
