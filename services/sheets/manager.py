import re
import gspread
from .client import GoogleSheetsClient
from .formatter import SheetFormatter

_URL_RE = re.compile(r'https?://[^\s"\']+')


def _normalize_url(url: str) -> str:
    return url.rstrip('/')

class SheetManager(GoogleSheetsClient):
    """
    High-level manager for Job Offer operations on Google Sheets.
    Inherits connection logic from GoogleSheetsClient.
    Uses SheetFormatter for styling.
    """
    def __init__(self, spreadsheet_name="Logistics Job Offers"):
        super().__init__(spreadsheet_name)
        self._ws_cache = None  # Fix 3: cache worksheets list across the run

    # --- Fix 3: worksheets cache ---

    def _get_worksheets(self):
        if self._ws_cache is None:
            self._ws_cache = self.spreadsheet.worksheets()
        return self._ws_cache

    def _invalidate_ws_cache(self):
        self._ws_cache = None

    def _find_worksheet(self, title):
        for ws in self._get_worksheets():
            if ws.title == title:
                return ws
        raise gspread.WorksheetNotFound(title)

    def get_or_create_worksheet(self, title):
        try:
            worksheet = self._find_worksheet(title)
        except gspread.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(title=title, rows=100, cols=20)
            self._invalidate_ws_cache()
            headers = ["Title", "Company", "Tags", "Status", "Link"]
            worksheet.append_row(headers)
            worksheet.freeze(rows=1)

        return worksheet

    # --- Fix 1: single scan for both slugs and records ---

    def get_all_existing_data(self):
        """Single API scan: returns (slugs_set, records_list) for all worksheets."""
        all_urls = set()
        all_records = []
        if not self.spreadsheet:
            return all_urls, all_records

        try:
            for ws in self._get_worksheets():
                print(f"Scanning sheet '{ws.title}'...")
                rows = ws.get_all_values(value_render_option='FORMULA')
                if not rows:
                    continue

                # Extract URLs
                for row in rows:
                    for cell in row:
                        if isinstance(cell, str) and "http" in cell:
                            for match in _URL_RE.findall(cell):
                                all_urls.add(_normalize_url(match))

                # Extract records
                headers = rows[0]
                try: t_idx = headers.index("Title")
                except: t_idx = -1
                try: c_idx = headers.index("Company")
                except: c_idx = -1
                try: tags_idx = headers.index("Tags")
                except: tags_idx = -1
                try: l_idx = headers.index("Link")
                except: l_idx = -1

                for row in rows[1:]:
                    all_records.append({
                        'title': (row[t_idx] if t_idx != -1 and t_idx < len(row) else "").strip(),
                        'company': (row[c_idx] if c_idx != -1 and c_idx < len(row) else "").strip(),
                        'tags': (row[tags_idx] if tags_idx != -1 and tags_idx < len(row) else "").strip(),
                        'link': (row[l_idx] if l_idx != -1 and l_idx < len(row) else "").strip(),
                    })

            print(f"Found {len(all_urls)} URLs and {len(all_records)} records across all sheets.")
        except Exception as e:
            print(f"Error scanning sheets: {e}")

        return all_urls, all_records

    def get_existing_slugs(self, worksheet):
        """Returns a set of normalized URLs from one sheet. Handles plain URLs and HYPERLINK formulas."""
        urls = set()
        try:
            rows = worksheet.get_all_values(value_render_option='FORMULA')
        except Exception:
            return set()

        for row in rows:
            for cell in row:
                if isinstance(cell, str) and "http" in cell:
                    for match in _URL_RE.findall(cell):
                        urls.add(_normalize_url(match))

        return urls

    def process_discards(self):
        """Moves rows with Status='DISCARD' or 'OUT' to a 'Trash' worksheet."""
        trash_ws = self.get_or_create_worksheet("Trash")

        for ws in self._get_worksheets():
            if ws.title == "Trash":
                continue
                
            try:
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
                        if status == "DISCARD" or status == "OUT":
                            should_discard = True
                    
                    if should_discard:
                        rows_to_move.append(row)
                    else:
                        rows_to_keep.append(row)
                
                if rows_to_move:
                    print(f"Moving {len(rows_to_move)} discarded/out offers from '{ws.title}' to Trash...")
                    trash_ws.append_rows(rows_to_move, value_input_option='USER_ENTERED')

                    print(f"Updating '{ws.title}' (removing discarded rows in bulk)...")
                    ws.clear()
                    SheetFormatter._clear_formatting(ws, self.spreadsheet)
                    ws.update(rows_to_keep, value_input_option='USER_ENTERED')
                    self.reorder_and_format(ws, preloaded_rows=rows_to_keep)
                        
            except Exception as e:
                print(f"Error processing discards in '{ws.title}': {e}")
                
        print("Formatting Trash sheet...")
        self.reorder_and_format(trash_ws)

    def reorder_and_format(self, worksheet, preloaded_rows=None):
        """Delegates to SheetFormatter. Pass preloaded_rows to skip the get_all_values read."""
        SheetFormatter.reorder_and_format(worksheet, self.spreadsheet, preloaded_rows=preloaded_rows)

    def add_offers(self, worksheet, offers, prepend=False):
        """Appends or prepends new offers to the worksheet, ensuring schema compliance."""
        rows_to_add = []
        for offer in offers:
            tags_val = offer.get("tags", "")
            if isinstance(tags_val, list):
                tags_val = ", ".join(str(t) for t in tags_val)
                
            row = [
                offer['title'],
                offer.get("company", ""),
                tags_val,
                "NEW", 
                offer.get("full_url", offer.get("link", "")) 
            ]
            rows_to_add.append(row)
        
        if not rows_to_add:
            print(f"No new offers to add to '{worksheet.title}'.")
            return

        print(f"Adding {len(rows_to_add)} offers to '{worksheet.title}'...")

        if prepend:
            # Get existing content with formulas
            existing_data = worksheet.get_all_values(value_render_option='FORMULA')
            
            headers = ["Title", "Company", "Tags", "Status", "Link"]
            normalized_existing = []
            
            if existing_data:
                old_headers = existing_data[0]
                col_map = {h: i for i, h in enumerate(old_headers)}
                
                for row in existing_data[1:]:
                    def get(col_name, default=""):
                        idx = col_map.get(col_name)
                        if idx is not None and idx < len(row):
                            return row[idx]
                        return default
                    
                    title_raw = get("Title")
                    link_val = get("Link")
                    
                    # Fallbacks logic from original file...
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
                    
                    norm_row = [
                        clean_title,
                        get("Company"),
                        get("Tags"),
                        get("Status"),
                        clean_link or get("Full URL")
                    ]
                    normalized_existing.append(norm_row)
            
            final_data = [headers] + rows_to_add + normalized_existing

            worksheet.clear()
            worksheet.update(final_data, value_input_option='USER_ENTERED')
            print(f"Prepended {len(rows_to_add)} offers and migrated {len(normalized_existing)} existing rows.")
            return final_data  # Fix 2: caller can pass this to reorder_and_format
        else:
            worksheet.append_rows(rows_to_add, value_input_option='USER_ENTERED')
            print(f"Appended {len(rows_to_add)} offers.")
            return None
