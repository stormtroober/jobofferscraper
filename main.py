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

def main():
    # Read links
    links_file = "links"
    urls = []
    if os.path.exists(links_file):
        with open(links_file, "r") as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
    if not urls:
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

    print("Fetching existing offers from all tabs to avoid duplicates...")
    existing_slugs = sheet_manager.get_all_existing_slugs()
    print(f"Found {len(existing_slugs)} existing offers across all tabs.")

    print("Fetching existing records for content deduplication...")
    existing_records = sheet_manager.get_all_existing_records()
    print(f"Loaded {len(existing_records)} existing records.")

    driver = get_driver(headless=True)
    
    try:
        for url in urls:
            print(f"\nProcessing: {url}")
            sheet_title = get_sheet_title(url)
            print(f"Target Worksheet: '{sheet_title}'")

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
                all_scraped = strategy.run(url)
            except Exception as e:
                print(f"Error scraping {url}: {e}")
                continue

            # Filtering Polish titles
            pre_filter_count = len(all_scraped)
            all_scraped = [offer for offer in all_scraped if not is_polish_title(offer['title'])]
            filtered_count = pre_filter_count - len(all_scraped)
            if filtered_count > 0:
                print(f"  Discarded {filtered_count} offers with Polish titles.")

            raw_offers = all_scraped[:limit]
            print(f"  Found {len(all_scraped)} valid offers. Processing top {len(raw_offers)}.")
            
            # Filter
            new_offers = []
            skipped_old = 0
            skipped_dup = 0
            
            # Fetch all existing records for robust deduplication
            # Structure: [{'title':..., 'company':..., 'tags':..., 'link':...}, ...]
            # Optimization: existing_records is now loaded once outside the loop and updated in-memory.
            # existing_records = sheet_manager.get_all_existing_records() 
            # print(f"  Loaded {len(existing_records)} existing records for deduplication.")
            
            for offer in raw_offers:
                # 1. Link Check
                if offer['full_url'] in existing_slugs:
                    skipped_dup += 1
                    continue
                
                # 2. Content Check (Tuple Match)
                is_content_dup = False
                for record in existing_records:
                    # Check overlap: Title + Company + Tags
                    # We compare stripped strings
                    if (offer['title'] == record['title'] and 
                        offer['company'] == record['company'] and
                        offer['tags'] == record['tags']):
                        is_content_dup = True
                        break
                
                if is_content_dup:
                    print(f"  Skipped content duplicate: {offer['title']} @ {offer['company']}")
                    skipped_dup += 1
                    continue
                
                new_offers.append(offer)
                # Add to set/records so we don't add reuse in same run
                existing_slugs.add(offer['full_url'])
                existing_records.append({
                    'title': offer['title'],
                    'company': offer['company'],
                    'tags': offer['tags'],
                    'link': offer['full_url']
                })
            
            print(f"  Filtered out: {skipped_dup} duplicates.")
            print(f"  New offers to add: {len(new_offers)}")
            
            worksheet = sheet_manager.get_or_create_worksheet(sheet_title)
            if new_offers:
                # We add them with prepend=True to keep newest on top
                sheet_manager.add_offers(worksheet, new_offers, prepend=True)
            
            # Reorder and Format (CVSENT on top, OUT at bottom, Colors)
            sheet_manager.reorder_and_format(worksheet)
            
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
