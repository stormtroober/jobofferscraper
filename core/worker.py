import concurrent.futures
from services.browser import get_driver
from strategies.factory import get_strategy

def process_url(url):
    """
    Worker function to scrape a single URL in its own browser instance.
    Returns (url, offers_list).
    """
    print(f"  [Worker] Starting: {url}")
    driver = get_driver(headless=True)
    offers = []
    
    try:
        limit = 50
        
        # Get Strategy from Factory
        strategy = get_strategy(url, driver)
        
        # Adjust limit for specific domains if needed
        if "theprotocol.it" in url:
            limit = 30
        
        # Scrape
        raw = strategy.run(url)
        raw_count = len(raw)
        
        # Slice top N
        offers = raw[:limit]
        
        msg = f"  [Worker] Done {url}: Found {raw_count} raw"
        msg += f". Keeping {len(offers)}."
        print(msg)
        
    except Exception as e:
        print(f"  [Worker] Error scraping {url}: {e}")
        offers = []
    finally:
        driver.quit()
        
    return url, offers
