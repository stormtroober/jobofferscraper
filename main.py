import os
import sys
import re
from urllib.parse import urlparse, parse_qs
from utils.browser import get_driver
from utils.sheet_manager import SheetManager
from strategies.justjoinit import JustJoinITStrategy
from strategies.nofluff import NoFluffJobsStrategy
from strategies.theprotocol import TheProtocolStrategy

def get_sheet_title(url):
    """Derives a readable sheet title from the URL parameters."""
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    
    parts = []
    
    # 1. Source (Domain)
    domain = parsed.netloc.replace("www.", "").split(".")[0]
    parts.append(domain)
    
    # 2. Extract keywords based on domain
    if "justjoin.it" in url:
        # /job-offers/krakow?keyword=junior...
        path_segments = parsed.path.split('/')
        if 'krakow' in path_segments:
            parts.append("krakow")
        elif len(path_segments) > 2:
             parts.append(path_segments[-1])
             
        keyword = qs.get("keyword", [""])[0]
        exp = qs.get("experience-level", [""])[0]
        if keyword: parts.append(f"kw-{keyword}")
        if exp: parts.append(f"exp-{exp}")
        
    elif "nofluffjobs.com" in url:
        # /pl/krakow?criteria=seniority%3Djunior
        # Extract location from path
        for segment in parsed.path.split('/'):
            if segment in ['pl', 'job']: continue
            if segment: parts.append(segment)
            
        # Extract criteria (e.g. seniority=junior)
        criteria = qs.get("criteria", [""])[0] # "seniority=junior"
        if criteria:
            cr_parts = criteria.split('=')
            if len(cr_parts) > 1:
                parts.append(cr_parts[1])
            else:
                parts.append(criteria)

    elif "theprotocol.it" in url:
        # /filtry/junior;p/krakow;wp
        # Splitting path: ['', 'filtry', 'junior;p', 'krakow;wp']
        # We need "junior", "krakow"
        path_segments = parsed.path.split('/')
        for seg in path_segments:
            if seg in ['', 'filtry']: continue
            # "junior;p" -> "junior"
            clean_seg = seg.split(';')[0]
            if clean_seg:
                parts.append(clean_seg)
        
        # Extract keyword (kw)
        kw = qs.get("kw", [""])[0]
        if kw:
            parts.append(f"kw-{kw}")
    else:
        # Fallback
        parts.append(parsed.path.replace('/', '-'))

    # Sanitize and join
    # Filter duplicates and empty
    clean_parts = []
    seen = set()
    for p in parts:
        p = p.lower().strip()
        if p and p not in seen:
            clean_parts.append(p)
            seen.add(p)
            
    title = "-".join(clean_parts)
    title = re.sub(r'[^\w\-]', '', title)
    return title[:100]

def is_recent(offer, days_limit=10):
    """Returns True if offer is recent (<= days_limit) or age is unknown/Fresh."""
    age_str = offer.get('posted_age', '').lower()
    
    if "new" in age_str:
        return True
        
    if "left" in age_str:
        # "27d left" -> typical validity is 30 days. So posted approx 3 days ago.
        # If "10d left" -> posted 20 days ago.
        # Wait, if validity is 30 days:
        # > 20d left = posted < 10 days ago.
        # checks: "11d left" (posted 19 days ago) -> False
        # checks: "21d left" (posted 9 days ago) -> True
        
        # Regex to find number
        match = re.search(r'(\d+)d', age_str)
        if match:
            days_left = int(match.group(1))
            days_posted_ago = 30 - days_left
            if days_posted_ago > days_limit:
                return False
            # Also if it says "1d left" -> posted 29 days ago -> False
            return True
            
    # For "1w ago" type strings if they exist (JustJoin usually shows "Xd left")
    return True

def is_polish_title(title):
    """
    Detects if the title is in Polish based on diacritics and keywords.
    Excludes 'ó' from diacritic check to avoid flagging city names like 'Kraków'.
    """
    title_lower = title.lower()
    
    # 1. Polish diacritics (excluding ó)
    # ą, ć, ę, ł, ń, ś, ź, ż
    if re.search(r'[ąćęłńśźż]', title_lower):
        return True
        
    # 2. Polish specific words (ASCII or with ó)
    polish_keywords = [
        'programista', 'starszy', 'specjalista', 'kierownik', 'analityk', 
        'architekt', 'konsultant', 'serwisant', 'doradca', 'praktykant', 
        'praca', 'zdalna', 'hybrydowa', 'stacjonarna', 'zespołu', r'ds\.',
        'asystent', 'ekspert', 'referent', 'koordynator'
    ]
    
    # Simple word bound check
    for keyword in polish_keywords:
        # \b matches word boundary
        if re.search(r'\b' + keyword + r'\b', title_lower):
            return True
            
    return False

def parse_links_file(filepath):
    """
    Parses the links file. Supports two formats:
    1. Legacy: List of URLs
    2. Grouped: INI-style sections
       [Sheet Name]
       url1
       url2
    
    Returns a list of dictionaries:
    [
      {'title': 'Sheet Name', 'urls': ['url1', 'url2']},
      {'title': None, 'urls': ['url3']} # Legacy/Ungrouped
    ]
    """
    groups = []
    current_group = {'title': None, 'urls': []}
    
    if not os.path.exists(filepath):
        return []
        
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
                
            # Check for Header [Title]
            if line.startswith("[") and line.endswith("]"):
                # Save previous group if it has URLs
                if current_group['urls']:
                    groups.append(current_group)
                
                # Start new group
                title = line[1:-1].strip()
                current_group = {'title': title, 'urls': []}
            else:
                # It's a URL
                current_group['urls'].append(line)
    
    # Add last group
    if current_group['urls']:
        groups.append(current_group)
        
    return groups

import argparse

def main():
    parser = argparse.ArgumentParser(description="Job Offer Scraper")
    parser.add_argument("--organize-only", action="store_true", help="Only organize sheets (process discards/reorder) without scraping")
    args = parser.parse_args()

    # Read links
    links_file = "links"
    link_groups = parse_links_file(links_file)
    
    if not link_groups:
        print("No URLs found in 'links' file. Please add URLs to the 'links' file.")
        return

    print("Initializing Google Sheets Manager...")
    try:
        sheet_manager = SheetManager()
    except Exception as e:
        print(f"Failed to initialize SheetManager: {e}")
        return

    print("Processing discards (moving to Trash)...")
    sheet_manager.process_discards()

    if args.organize_only:
        print("\n=== ORGANIZE ONLY MODE ===")
        print("Skipping scraping. Reordering and verifying sheets based on 'links' groups...")
        
        for group in link_groups:
            sheet_title = group['title']
            if not sheet_title and group['urls']:
                sheet_title = get_sheet_title(group['urls'][0])
            
            if sheet_title:
                try:
                    worksheet = sheet_manager.get_or_create_worksheet(sheet_title)
                    sheet_manager.reorder_and_format(worksheet)
                except Exception as e:
                    print(f"Error processing sheet '{sheet_title}': {e}")
        
        print("Organization complete.")
        return

    print("Fetching existing offers from all tabs to avoid duplicates...")
    existing_slugs = sheet_manager.get_all_existing_slugs()
    print(f"Found {len(existing_slugs)} existing offers across all tabs.")

    print("Fetching existing records for content deduplication...")
    existing_records = sheet_manager.get_all_existing_records()
    print(f"Loaded {len(existing_records)} existing records.")

    driver = get_driver(headless=True)
    
    # Statistics for the summary
    stats = []

    try:
        for group in link_groups:
            # Determine Sheet Title
            sheet_title = group['title']
            
            if not sheet_title:
                if group['urls']:
                    # Fallback to deriving from first URL
                    sheet_title = get_sheet_title(group['urls'][0])
                else:
                    continue 

            print(f"\n{'='*60}")
            print(f"Processing Group: '{sheet_title}'")
            print(f"Sources: {len(group['urls'])}")
            for i, u in enumerate(group['urls'], 1):
                print(f"  {i}. {u}")
            print(f"{'-'*60}")
            
            # Aggregate offers from ALL URLs in this group
            combined_offers = []
            
            for index, url in enumerate(group['urls'], 1):
                print(f"\n  [{index}/{len(group['urls'])}] Fetching: {url}")
                
                limit = 50
                # Determine Strategy
                if "nofluffjobs.com" in url:
                    strategy = NoFluffJobsStrategy(driver)
                elif "theprotocol.it" in url:
                    strategy = TheProtocolStrategy(driver)
                    limit = 30
                else:
                    strategy = JustJoinITStrategy(driver)
                
                # Scrape
                try:
                    scraped = strategy.run(url)
                    raw_count = len(scraped)
                    
                    # Filtering Polish titles (Per URL)
                    scraped = [offer for offer in scraped if not is_polish_title(offer['title'])]
                    filtered_polish_count = raw_count - len(scraped)

                    # Slice top N per URL
                    scraped = scraped[:limit]
                    
                    combined_offers.extend(scraped)
                    
                    msg = f"        Found {raw_count} raw offers."
                    if filtered_polish_count > 0:
                        msg += f" Discarded {filtered_polish_count} (Polish)."
                    print(msg)
                    
                except Exception as e:
                    print(f"        Error scraping: {e}")
                    continue

            print(f"\n  Total candidates for '{sheet_title}': {len(combined_offers)}")
            
            # Now we filter duplicates for the whole batch
            new_offers = []
            skipped_dup = 0
            
            for offer in combined_offers:
                # 1. Link Check
                if offer['full_url'] in existing_slugs:
                    skipped_dup += 1
                    continue
                
                # 2. Content Check (Tuple Match)
                is_content_dup = False
                for record in existing_records:
                    if (offer['title'] == record['title'] and 
                        offer['company'] == record['company'] and
                        offer['tags'] == record['tags']):
                        is_content_dup = True
                        break
                
                if is_content_dup:
                    # print(f"    Skipped content duplicate: {offer['title']}")
                    skipped_dup += 1
                    continue
                
                new_offers.append(offer)
                existing_slugs.add(offer['full_url'])
                existing_records.append({
                    'title': offer['title'],
                    'company': offer['company'],
                    'tags': offer['tags'],
                    'link': offer['full_url']
                })
            
            print(f"  Filtered duplicates: {skipped_dup}")
            print(f"  New offers to add: {len(new_offers)}")
            
            worksheet = sheet_manager.get_or_create_worksheet(sheet_title)
            if new_offers:
                sheet_manager.add_offers(worksheet, new_offers, prepend=True)
            
            sheet_manager.reorder_and_format(worksheet)
            
            # Add to stats
            stats.append({
                'group': sheet_title,
                'new': len(new_offers),
                'total_candidates': len(combined_offers)
            })
            
    finally:
        driver.quit()
        
    # === FINAL SUMMARY ===
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

if __name__ == "__main__":
    main()
