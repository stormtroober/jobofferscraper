import time
from bs4 import BeautifulSoup
from .base import ScrapingStrategy

class BuiltInStrategy(ScrapingStrategy):
    def fetch(self, url):
        self.driver.get(url)
        # BuiltIn often has a loading state or verifies browser
        time.sleep(3) 
        return self.driver.page_source

    def parse(self, soup):
        offers = []
        
        # Select all job cards with data-id="job-card"
        cards = soup.find_all('div', attrs={'data-id': 'job-card'})
        
        for card in cards:
            try:
                # Title and Link
                title_tag = card.find('a', attrs={'data-id': 'job-card-title'})
                if not title_tag:
                    continue
                    
                title = title_tag.get_text(strip=True)
                relative_link = title_tag.get('href')
                
                if relative_link and relative_link.startswith('/'):
                    full_url = f"https://builtin.com{relative_link}"
                elif relative_link:
                    full_url = relative_link
                else:
                    full_url = ""
                    
                slug = full_url.split('/')[-1] if full_url else ""
                
                # Company
                company_tag = card.find('a', attrs={'data-id': 'company-title'})
                company = company_tag.get_text(strip=True) if company_tag else "Unknown"
                
                # Tags - typically not easily available as a simple list in the card summary on BuiltIn
                # We'll leave it empty or try to find minimal info
                tags = ""
                
                offers.append({
                    'title': title,
                    'company': company,
                    'tags': tags,
                    'link_slug': slug,
                    'full_url': full_url
                })
            except Exception as e:
                print(f"Error parsing offer in BuiltInStrategy: {e}")
                continue
        
        return offers

    def run(self, url):
        all_offers = []
        current_url = url
        
        while current_url:
            print(f"Scraping BuiltIn page: {current_url}")
            html = self.fetch(current_url)
            soup = BeautifulSoup(html, 'html.parser')
            
            offers = self.parse(soup)
            all_offers.extend(offers)
            print(f"Found {len(offers)} offers on this page.")
            
            # Find next page
            # Example: <a href="...?page=2" aria-label="Go to Next Page">
            next_button = soup.find('a', attrs={'aria-label': 'Go to Next Page'})
            if next_button and next_button.get('href'):
                href = next_button.get('href')
                if href.startswith('/'):
                    current_url = f"https://builtin.com{href}"
                else:
                    current_url = href
                
                # Short pause to be polite
                time.sleep(2)
            else:
                current_url = None
                
        return all_offers
