import os
import json
import gspread
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2 import service_account

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

CREDS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

class GoogleSheetsClient:
    def __init__(self, spreadsheet_name="Logistics Job Offers"):
        self.client = None
        self.spreadsheet = None
        self.spreadsheet_name = spreadsheet_name
        self._authenticate()
        self._open_spreadsheet()

    def _authenticate(self):
        creds = None
        
        # 1. Try Environment Variable (Best for Cloud/Docker)
        env_creds = os.environ.get("GCP_SERVICE_ACCOUNT_CREDENTIALS")
        if env_creds:
            print("Using credentials from Environment Variable 'GCP_SERVICE_ACCOUNT_CREDENTIALS'.")
            try:
                creds_info = json.loads(env_creds)
                creds = service_account.Credentials.from_service_account_info(
                    creds_info, scopes=SCOPES)
                self.client = gspread.authorize(creds)
                return
            except json.JSONDecodeError:
                print("Error: GCP_SERVICE_ACCOUNT_CREDENTIALS is not valid JSON.")
            except Exception as e:
                print(f"Error loading credentials from Env Var: {e}")

        # 2. Try File (Local Development)
        if os.path.exists(CREDS_FILE):
            with open(CREDS_FILE, 'r') as f:
                try:
                    creds_data = json.load(f)
                    cred_type = creds_data.get('type')
                except json.JSONDecodeError:
                    print("Error: credentials.json is not valid JSON.")
                    return

            if cred_type == 'service_account':
                print("Using Service Account credentials from file.")
                creds = service_account.Credentials.from_service_account_file(
                    CREDS_FILE, scopes=SCOPES)
            else:
                print("Using OAuth credentials.")
                if os.path.exists(TOKEN_FILE):
                    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
                
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                    else:
                        flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
                        # Force offline access to get a refresh token
                        creds = flow.run_local_server(port=0, access_type='offline', prompt='consent')
                    
                    with open(TOKEN_FILE, "w") as token:
                        token.write(creds.to_json())
        else:
            # If we are here, we have neither Env Var nor File
            raise FileNotFoundError(f"Credentials not found! Set GCP_SERVICE_ACCOUNT_CREDENTIALS env var or place '{CREDS_FILE}' in the directory.")

        self.client = gspread.authorize(creds)

    def _open_spreadsheet(self):
        try:
            self.spreadsheet = self.client.open(self.spreadsheet_name)
            print(f"Opened spreadsheet '{self.spreadsheet_name}': {self.spreadsheet.url}")
        except gspread.SpreadsheetNotFound:
            print(f"Spreadsheet '{self.spreadsheet_name}' not found. Creating new...")
            self.spreadsheet = self.client.create(self.spreadsheet_name)
            # If using Service Account, you might need to share it with your personal email here
            # self.spreadsheet.share('your_email@gmail.com', perm_type='user', role='writer')
            print(f"Created spreadsheet: {self.spreadsheet.url}")
