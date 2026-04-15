import gspread
from .client import GoogleSheetsClient
from .formatter import SheetFormatter

class SheetManager(GoogleSheetsClient):
    """
    High-level manager for Job Offer operations on Google Sheets.
    Inherits connection logic from GoogleSheetsClient.
    Uses SheetFormatter for styling.
    """
    def __init__(self, spreadsheet_name="Job Offers Scraper"):
        super().__init__(spreadsheet_name)

    def get_or_create_worksheet(self, title):
        try:
            worksheet = self.spreadsheet.worksheet(title)
        except gspread.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(title=title, rows=100, cols=20)
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
            rows = worksheet.get_all_values(value_render_option='FORMULA')
        except Exception:
            return set()
            
        # Robust scan: Look for http links in ANY cell
        for row in rows:
            for cell in row:
                if isinstance(cell, str) and "http" in cell:
                    if "HYPERLINK" in cell:
                        try:
                            parts = cell.split('"')
                            for p in parts:
                                if "http" in p:
                                    urls.add(p)
                        except:
                            pass
                    else:
                        if "://" in cell:
                            raw_url = str(cell).strip()
                            urls.add(raw_url)
        
        return urls

    def get_all_existing_records(self):
        """Returns a list of all existing records (title, company, tags, link) from ALL worksheets."""
        all_records = []
        if not self.spreadsheet:
            return all_records
            
        try:
            worksheets = self.spreadsheet.worksheets()
            for ws in worksheets:
                rows = ws.get_all_values()
                if not rows: continue
                
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
                    title = row[t_idx] if t_idx != -1 and t_idx < len(row) else ""
                    company = row[c_idx] if c_idx != -1 and c_idx < len(row) else ""
                    tags = row[tags_idx] if tags_idx != -1 and tags_idx < len(row) else ""
                    link = row[l_idx] if l_idx != -1 and l_idx < len(row) else ""
                    
                    all_records.append({
                        'title': title.strip(),
                        'company': company.strip(),
                        'tags': tags.strip(),
                        'link': link.strip()
                    })
                    
        except Exception as e:
            print(f"Error scanning sheets for full records: {e}")
            
        return all_records

    def get_saved_offers(self):
        """
        Returns a list of dicts for every row whose Status == 'SAVE'
        across all worksheets (Trash excluded).

        Each dict: {title, company, tags, link, sheet}
        """
        results = []
        if not self.spreadsheet:
            return results

        try:
            worksheets = self.spreadsheet.worksheets()
            for ws in worksheets:
                if ws.title == "Trash":
                    continue

                rows = ws.get_all_values()
                if not rows:
                    continue

                header = rows[0]
                col = {h: i for i, h in enumerate(header)}

                t_idx  = col.get("Title", -1)
                c_idx  = col.get("Company", -1)
                tg_idx = col.get("Tags", -1)
                s_idx  = col.get("Status", -1)
                l_idx  = col.get("Link", -1)

                if s_idx == -1:
                    continue

                for row in rows[1:]:
                    if len(row) <= s_idx:
                        continue
                    status = row[s_idx].strip().upper()
                    if status != "SAVE":
                        continue

                    def _get(idx):
                        return row[idx].strip() if idx != -1 and idx < len(row) else ""

                    results.append({
                        "title":   _get(t_idx),
                        "company": _get(c_idx),
                        "tags":    _get(tg_idx),
                        "link":    _get(l_idx),
                        "sheet":   ws.title,
                    })

        except Exception as e:
            print(f"Error fetching SAVE offers: {e}")

        return results

    def process_discards(self):
        """Moves rows with Status='DISCARD' or 'OUT' to a 'Trash' worksheet."""
        trash_ws = self.get_or_create_worksheet("Trash")
        
        for ws in self.spreadsheet.worksheets():
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
                    self.reorder_and_format(ws)
                        
            except Exception as e:
                print(f"Error processing discards in '{ws.title}': {e}")
                
        print("Formatting Trash sheet...")
        self.reorder_and_format(trash_ws)

    def reorder_and_format(self, worksheet):
        """Delegates to SheetFormatter."""
        # We pass self.spreadsheet because _clear_formatting needs it for batch_update
        SheetFormatter.reorder_and_format(worksheet, self.spreadsheet)

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
        else:
            worksheet.append_rows(rows_to_add, value_input_option='USER_ENTERED')
            print(f"Appended {len(rows_to_add)} offers.")
