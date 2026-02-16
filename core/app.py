import argparse
import concurrent.futures
from services.sheets import SheetManager
from core.parsers import parse_links_file, get_sheet_title
from core.worker import process_url

class JobScraperApp:
    def __init__(self):
        self.args = self._parse_args()
        self.sheet_manager = None
        self.link_groups = []
        
    def _parse_args(self):
        parser = argparse.ArgumentParser(description="Job Offer Scraper")
        parser.add_argument("--organize-only", action="store_true", help="Only organize sheets (process discards/reorder) without scraping")
        return parser.parse_args()

    def run(self):
        # 1. Load Config
        if not self._load_config():
            return

        # 2. Init Services
        if not self._init_services():
            return

        # 3. Process Discards
        print("Processing discards (moving to Trash)...")
        self.sheet_manager.process_discards()

        # 4. Organize Only Mode
        if self.args.organize_only:
            self._run_organize_only()
            return

        # 5. Full Scrape Mode
        self._run_full_scrape()

    def _load_config(self):
        links_file = "links.json"
        self.link_groups = parse_links_file(links_file)
        if not self.link_groups:
            print(f"No groups found in '{links_file}'. Please check the file content.")
            return False
        return True

    def _init_services(self):
        print("Initializing Google Sheets Manager...")
        try:
            self.sheet_manager = SheetManager()
            return True
        except Exception as e:
            print(f"Failed to initialize SheetManager: {e}")
            return False

    def _run_organize_only(self):
        print("\n=== ORGANIZE ONLY MODE ===")
        print("Skipping scraping. Reordering and verifying sheets based on 'links' groups...")
        
        for group in self.link_groups:
            sheet_title = group['title']
            if not sheet_title and group['urls']:
                sheet_title = get_sheet_title(group['urls'][0])
            
            if sheet_title:
                try:
                    worksheet = self.sheet_manager.get_or_create_worksheet(sheet_title)
                    self.sheet_manager.reorder_and_format(worksheet)
                except Exception as e:
                    print(f"Error processing sheet '{sheet_title}': {e}")
        
        print("Organization complete.")

    def _run_full_scrape(self):
        print("Fetching existing offers from all tabs to avoid duplicates...")
        existing_slugs = self.sheet_manager.get_all_existing_slugs()
        print(f"Found {len(existing_slugs)} existing offers across all tabs.")

        print("Fetching existing records for content deduplication...")
        existing_records = self.sheet_manager.get_all_existing_records()
        print(f"Loaded {len(existing_records)} existing records.")

        # Gather URLs
        all_urls = []
        for group in self.link_groups:
            all_urls.extend(group['urls'])
        unique_urls = list(set(all_urls))

        print(f"\n{'='*60}")
        print(f"STARTING PARALLEL SCRAPING")
        print(f"Unique URLs to process: {len(unique_urls)}")
        print(f"Max Workers: 8")
        print(f"{'='*60}")

        # Scrape
        scraped_data = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            future_to_url = {executor.submit(process_url, url): url for url in unique_urls}
            
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    _, offers = future.result()
                    scraped_data[url] = offers
                except Exception as e:
                    print(f"CRITICAL ERROR retrieving results for {url}: {e}")
                    scraped_data[url] = []

        print(f"\n{'='*60}")
        print("Scraping complete. Updating Sheets...")
        print(f"{'='*60}")

        self._update_sheets(scraped_data, existing_slugs, existing_records)

    def _update_sheets(self, scraped_data, existing_slugs, existing_records):
        stats = []
        
        for group in self.link_groups:
            sheet_title = group['title']
            if not sheet_title:
                if group['urls']:
                    sheet_title = get_sheet_title(group['urls'][0])
                else:
                    continue 
            
            combined_offers = []
            for url in group['urls']:
                if url in scraped_data:
                    combined_offers.extend(scraped_data[url])
            
            print(f"\nProcessing Group: '{sheet_title}'")
            print(f"  Total candidates: {len(combined_offers)}")
            
            new_offers, skipped_dup = self._filter_offers(combined_offers, existing_slugs, existing_records)
            
            print(f"  Filtered duplicates: {skipped_dup}")
            print(f"  New offers to add: {len(new_offers)}")
            
            worksheet = self.sheet_manager.get_or_create_worksheet(sheet_title)
            if new_offers:
                self.sheet_manager.add_offers(worksheet, new_offers, prepend=True)
            
            self.sheet_manager.reorder_and_format(worksheet)
            
            stats.append({
                'group': sheet_title,
                'new': len(new_offers),
                'total_candidates': len(combined_offers)
            })
            
        self._print_summary(stats)

    def _filter_offers(self, combined_offers, existing_slugs, existing_records):
        new_offers = []
        skipped_dup = 0
        
        for offer in combined_offers:
            # 1. Link Check
            if offer['full_url'] in existing_slugs:
                skipped_dup += 1
                continue
            
            # 2. Content Check
            is_content_dup = False
            for record in existing_records:
                if (offer['title'] == record['title'] and 
                    offer['company'] == record['company'] and
                    offer['tags'] == record['tags']):
                    is_content_dup = True
                    break
            
            if is_content_dup:
                skipped_dup += 1
                continue
            
            print(f"    [NEW] Adding: {offer['title'][:50]}")
            new_offers.append(offer)
            existing_slugs.add(offer['full_url'])
            existing_records.append({
                'title': offer['title'],
                'company': offer['company'],
                'tags': offer['tags'],
                'link': offer['full_url']
            })
            
        return new_offers, skipped_dup

    def _print_summary(self, stats):
        print("\n\n" + "="*60)
        print("FINAL SUMMARY REPORT")
        print("="*60)
        if not stats:
            print("No groups processed.")
        else:
            total_new = 0
            for s in stats:
                print(f"[{s['group']}]".ljust(30) + f": {s['new']} new offers (from {s['total_candidates']} candidates)")
                total_new += s['new']
            print("-" * 60)
            if total_new > 0:
                print(f"TOTAL NEW OFFERS: {total_new}")
            else:
                print("NO NEW OFFERS FOUND.")
        print("="*60 + "\n")
