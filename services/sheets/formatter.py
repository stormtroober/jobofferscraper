class SheetFormatter:
    """Methods for formatting and reordering worksheets."""
    
    @staticmethod
    def _clear_formatting(worksheet, spreadsheet):
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
            spreadsheet.batch_update(body)
        except Exception as e:
            print(f"Error clearing formatting for '{worksheet.title}': {e}")

    @staticmethod
    def reorder_and_format(worksheet, spreadsheet):
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
            SheetFormatter._clear_formatting(worksheet, spreadsheet)
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
