from bs4 import BeautifulSoup
from .base import ScrapingStrategy
import re

class TheProtocolStrategy(ScrapingStrategy):
    def fetch(self, url):
        print(f"Fetching {url}")
        self.driver.get(url)
        # We might need to wait for content to load, but usually getting page_source after get() works for simple interactions
        # If dynamic loading is an issue, we might need explicitly wait for #main-offers-listing
        return self.driver.page_source

    def parse(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Locate the main container for offers
        offers_container = soup.find(id='main-offers-listing')
        if not offers_container:
            print("Could not find #main-offers-listing")
            return []

        # Find all offer links
        # Based on analysis: <a class="a4pzt2q" ...>
        offer_elements = offers_container.select('a[data-test="list-item-offer"]')
        
        print(f"Found {len(offer_elements)} raw offers.")
        
        offers = []
        for offer_el in offer_elements:
            try:
                # Link
                relative_link = offer_el.get('href')
                if relative_link:
                    # Strip params
                    relative_link = relative_link.split('?')[0]
                    full_url = f"https://theprotocol.it{relative_link}"
                else:
                    full_url = "Unknown"
                
                # Title
                title_el = offer_el.select_one('#offer-title')
                title = title_el.get_text(strip=True) if title_el else "Unknown"
                
                # Company
                company_el = offer_el.select_one('[data-test="text-employerName"]')
                company = company_el.get_text(strip=True) if company_el else "Unknown"
                
                # Tags
                tags_elements = offer_el.select('[data-test="chip-expectedTechnology"]')
                tags_list = [t.get_text(strip=True) for t in tags_elements]
                tags = ", ".join(tags_list)
                
                offers.append({
                    'title': title,
                    'company': company,
                    'tags': tags,
                    'link': full_url,
                    'full_url': full_url
                })
            except Exception as e:
                print(f"Error parsing offer: {e}")
                continue
                
        return offers

    def run(self, url):
        html_content = self.fetch(url)
        # No Markdown conversion needed for this strategy as we parse HTML directly
        return self.parse(html_content)
