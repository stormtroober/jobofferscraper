import os.path
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

class SheetManager:
    def __init__(self, spreadsheet_name="Job Offers Scraper"):
        self.client = None
        self.spreadsheet = None
        self.spreadsheet_name = spreadsheet_name
        self._authenticate()
        self._open_spreadsheet()

    def _authenticate(self):
        creds = None
        
        if os.path.exists(CREDS_FILE):
            with open(CREDS_FILE, 'r') as f:
                try:
                    creds_data = json.load(f)
                    cred_type = creds_data.get('type')
                except json.JSONDecodeError:
                    print("Error: credentials.json is not valid JSON.")
                    return

            if cred_type == 'service_account':
                print("Using Service Account credentials.")
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
                        creds = flow.run_local_server(port=0)
                    
                    with open(TOKEN_FILE, "w") as token:
                        token.write(creds.to_json())
        else:
            raise FileNotFoundError(f"{CREDS_FILE} not found!")

        self.client = gspread.authorize(creds)

    def _open_spreadsheet(self):
        try:
            self.spreadsheet = self.client.open(self.spreadsheet_name)
        except gspread.SpreadsheetNotFound:
            print(f"Spreadsheet '{self.spreadsheet_name}' not found. Creating new...")
            self.spreadsheet = self.client.create(self.spreadsheet_name)
            # If using Service Account, you might need to share it with your personal email here
            # self.spreadsheet.share('your_email@gmail.com', perm_type='user', role='writer')
            print(f"Created spreadsheet: {self.spreadsheet.url}")

    def get_or_create_worksheet(self, title):
        try:
            worksheet = self.spreadsheet.worksheet(title)
        except gspread.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(title=title, rows=100, cols=20)
            # Initialize headers
            # Initialize headers
            headers = ["Title", "Company", "Tags", "Status", "Link"]
            worksheet.append_row(headers)
            worksheet.freeze(rows=1)
            
        return worksheet

    def get_all_existing_slugs(self):
        """Returns a set of all full_urls present in ALL worksheets AND Trash to avoid cross-tab duplicates."""
        all_urls = set()
        if not self.spreadsheet:
            return all_urls
            
        try:
            worksheets = self.spreadsheet.worksheets()
            for ws in worksheets:
                print(f"Scanning sheet '{ws.title}' for existing offers...")
                urls = self.get_existing_slugs(ws)
                all_urls.update(urls)
                print(f"  Found {len(urls)} urls in '{ws.title}'.")
        except Exception as e:
            print(f"Error scanning sheets for duplicates: {e}")
            
        return all_urls

    def get_existing_slugs(self, worksheet):
        """Returns a set of existing link slugs (or full URLs) from the sheet. Robust scan."""
        urls = set()
        try:
            # Read all text data (formulas not needed if we search for raw URL text, 
            # BUT if they are hyperlinks we might need formulas.
            # However, we stored Full URL in a separate column "Link" as text in recent versions.
            # In old versions it was in formula.
            # Safest: Read formulas.
            rows = worksheet.get_all_values(value_render_option='FORMULA')
        except Exception:
            return set()
            
        # Robust scan: Look for http links in ANY cell
        # This covers Trash, old schemas, new schemas, mixed content.
        for row in rows:
            for cell in row:
                if isinstance(cell, str) and "http" in cell:
                    # If it's a formula =HYPERLINK("url", "label")
                    if "HYPERLINK" in cell:
                        try:
                            parts = cell.split('"')
                            for p in parts:
                                if "http" in p:
                                    urls.add(p)
                        except:
                            pass
                    else:
                        # Raw URL
                        # minimal validation
                        if "://" in cell:
                            raw_url = cell.strip()
                            clean_url = raw_url.split('?')[0]
                            urls.add(clean_url)
        
        return urls

    def get_all_existing_records(self):
        """Returns a list of all existing records (title, company, tags, link) from ALL worksheets to avoid content duplicates."""
        all_records = []
        if not self.spreadsheet:
            return all_records
            
        try:
            worksheets = self.spreadsheet.worksheets()
            for ws in worksheets:
                # We include Trash in deduplication to avoid re-adding previously discarded offers?
                # Yes, user said "non controllare duplicati solo in base a link ma aanche a sovrappisozione completa di tutti i campi"
                # implying global uniqueness.
                
                rows = ws.get_all_values()
                if not rows: continue
                
                headers = rows[0]
                # Map headers
                try: t_idx = headers.index("Title")
                except: t_idx = -1
                try: c_idx = headers.index("Company")
                except: c_idx = -1
                try: tags_idx = headers.index("Tags")
                except: tags_idx = -1
                try: 
                    # Prefer "Link" column, but fallback to extracting from Title if needed?
                    # Current add_offers puts link in "Link".
                    l_idx = headers.index("Link")
                except: l_idx = -1
                
                for row in rows[1:]:
                    title = row[t_idx] if t_idx != -1 and t_idx < len(row) else ""
                    company = row[c_idx] if c_idx != -1 and c_idx < len(row) else ""
                    tags = row[tags_idx] if tags_idx != -1 and tags_idx < len(row) else ""
                    link = row[l_idx] if l_idx != -1 and l_idx < len(row) else ""
                    
                    # Normalize for comparison
                    all_records.append({
                        'title': title.strip(),
                        'company': company.strip(),
                        'tags': tags.strip(),
                        'link': link.strip()
                    })
                    
        except Exception as e:
            print(f"Error scanning sheets for full records: {e}")
            
        return all_records

    def _clear_formatting(self, worksheet):
        """Clears all formatting from the worksheet to prevent ghost colors."""
        try:
            body = {
                "requests": [
                    {
                        "updateCells": {
                            "range": {
                                "sheetId": worksheet.id
                            },
                            "fields": "userEnteredFormat"
                        }
                    }
                ]
            }
            self.spreadsheet.batch_update(body)
        except Exception as e:
            print(f"Error clearing formatting for '{worksheet.title}': {e}")

    def process_discards(self):
        """Moves rows with Status='DISCARD' or 'OUT' to a 'Trash' worksheet."""
        trash_ws = self.get_or_create_worksheet("Trash")
        
        for ws in self.spreadsheet.worksheets():
            if ws.title == "Trash":
                continue
                
            try:
                # Read with formulas to preserve data integrity during rewrite
                rows = ws.get_all_values(value_render_option='FORMULA')
                if not rows: continue
                
                header = rows[0]
                try:
                    status_idx = header.index("Status")
                except ValueError:
                    continue
                
                rows_to_move = []
                rows_to_keep = [header]
                
                for row in rows[1:]:
                    should_discard = False
                    if len(row) > status_idx:
                        status = row[status_idx].strip().upper()
                        # Move both DISCARD and OUT to trash
                        if status == "DISCARD" or status == "OUT":
                            should_discard = True
                    
                    if should_discard:
                        rows_to_move.append(row)
                    else:
                        rows_to_keep.append(row)
                
                if rows_to_move:
                    print(f"Moving {len(rows_to_move)} discarded/out offers from '{ws.title}' to Trash...")
                    trash_ws.append_rows(rows_to_move, value_input_option='USER_ENTERED')
                    
                    # Batch delete by rewriting the sheet
                    print(f"Updating '{ws.title}' (removing discarded rows in bulk)...")
                    ws.clear()
                    self._clear_formatting(ws)
                    ws.update(rows_to_keep, value_input_option='USER_ENTERED')
                    self.reorder_and_format(ws)
                        
            except Exception as e:
                print(f"Error processing discards in '{ws.title}': {e}")
                
        # Format the Trash sheet as well (so OUT are red)
        print("Formatting Trash sheet...")
        self.reorder_and_format(trash_ws)

    def reorder_and_format(self, worksheet):
        """
        Sorts: CVSENT -> SAVE -> Others -> OUT.
        Colors: 
         - CVSENT: Green
         - SAVE: Yellow/Orange
         - OUT: Red
        """
        try:
            rows = worksheet.get_all_values(value_render_option='FORMULA')
            if not rows: return

            header = rows[0]
            data = rows[1:]

            try:
                status_idx = header.index("Status")
            except ValueError:
                return

            cvsent_rows = []
            save_rows = []
            out_rows = []
            other_rows = []

            for row in data:
                if len(row) > status_idx:
                    status = row[status_idx].strip().upper()
                    if "CVSENT" in status:
                        cvsent_rows.append(row)
                    elif "SAVE" in status:
                        save_rows.append(row)
                    elif "OUT" in status:
                        out_rows.append(row)
                    else:
                        other_rows.append(row)
                else:
                    other_rows.append(row)

            # Order: CVSENT -> SAVE -> Others -> OUT
            final_rows = [header] + cvsent_rows + save_rows + other_rows + out_rows
            
            # Write data back
            worksheet.clear()
            self._clear_formatting(worksheet)
            worksheet.update(final_rows, value_input_option='USER_ENTERED')
            
            # Formatting
            fmt_header = {"textFormat": {"bold": True}}
            fmt_green = {"backgroundColor": {"red": 0.85, "green": 0.93, "blue": 0.83}} # Light Green
            fmt_yellow = {"backgroundColor": {"red": 1.0, "green": 0.95, "blue": 0.8}}  # Light Yellow/Orange for SAVE
            fmt_red = {"backgroundColor": {"red": 0.96, "green": 0.8, "blue": 0.8}}     # Light Red
            fmt_white = {"backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}}    # White/Reset
            
            batch = []
            
            # Header
            batch.append({"range": "A1:Z1", "format": fmt_header})
            
            current_row = 2
            
            # Helper to add format range
            def add_fmt(row_list, fmt):
                nonlocal current_row
                if row_list:
                    end_row = current_row + len(row_list) - 1
                    batch.append({"range": f"A{current_row}:Z{end_row}", "format": fmt})
                    current_row = end_row + 1

            add_fmt(cvsent_rows, fmt_green)
            add_fmt(save_rows, fmt_yellow)
            add_fmt(other_rows, fmt_white)
            add_fmt(out_rows, fmt_red)
                
            try:
                worksheet.batch_format(batch)
                print(f"Reordered and formatted '{worksheet.title}'.")
            except AttributeError:
                pass
                
        except Exception as e:
            print(f"Error reordering/formatting '{worksheet.title}': {e}")
            
    def add_offers(self, worksheet, offers, prepend=False):
        """Appends or prepends new offers to the worksheet, ensuring schema compliance."""
        rows_to_add = []
        for offer in offers:
            # ["Title", "Company", "Tags", "Status", "Link"]
            row = [
                offer['title'],
                offer.get("company", ""),
                # Salary, Location removed
                offer.get("tags", ""),
                "NEW", # Status (User requested: between tags and link)
                offer.get("full_url", offer.get("link", "")) # Link backup
            ]
            rows_to_add.append(row)
        
        if not rows_to_add:
            print(f"No new offers to add to '{worksheet.title}'.")
            return

        print(f"Adding {len(rows_to_add)} offers to '{worksheet.title}'...")

        if prepend:
            # Get existing content with formulas to preserve/migrate data
            existing_data = worksheet.get_all_values(value_render_option='FORMULA')
            
            headers = ["Title", "Company", "Tags", "Status", "Link"]
            normalized_existing = []
            
            if existing_data:
                old_headers = existing_data[0]
                # Identify columns
                try: 
                    t_idx = old_headers.index("Title")
                except: t_idx = 0
                
                try: l_idx = old_headers.index("Link")
                except: l_idx = -1
                
                col_map = {h: i for i, h in enumerate(old_headers)}
                
                for row in existing_data[1:]:
                    def get(col_name, default=""):
                        idx = col_map.get(col_name)
                        if idx is not None and idx < len(row):
                            return row[idx]
                        return default
                    
                    # Special handling for Title (Link Extraction)
                    title_raw = get("Title")
                    link_val = get("Link")
                    
                    if "Title" not in col_map and row:
                        title_raw = row[0]
                    
                    clean_title = title_raw
                    clean_link = link_val
                    
                    if '=HYPERLINK' in str(title_raw):
                        try:
                            parts = title_raw.split('"')
                            if len(parts) >= 4:
                                clean_link = parts[1]
                                clean_title = parts[3]
                        except:
                            pass
                    
                    # Construct normalized row WITHOUT Age, Salary, Location
                    norm_row = [
                        clean_title,
                        get("Company"),
                        # Salary removed
                        # Location removed
                        get("Tags"),
                        get("Status"),
                        clean_link or get("Full URL")
                    ]
                    normalized_existing.append(norm_row)
            
            final_data = [headers] + rows_to_add + normalized_existing
            
            worksheet.clear()
            worksheet.update(final_data, value_input_option='USER_ENTERED')
            print(f"Prepended {len(rows_to_add)} offers and migrated {len(normalized_existing)} existing rows (Schema Updated).")
        else:
            worksheet.append_rows(rows_to_add, value_input_option='USER_ENTERED')
            print(f"Appended {len(rows_to_add)} offers.")
