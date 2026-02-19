import re
import os
from bs4 import BeautifulSoup
from .base import ScrapingStrategy
from services.converter import html_to_markdown, sanitize_filename

class JustJoinITStrategy(ScrapingStrategy):
    def fetch(self, url):
        self.driver.get(url)
        import time
        time.sleep(5) # Wait for SPA to render
        return self.driver.page_source

    def parse(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        offers = []

        # Find all job offer links
        # JustJoinIT uses <a> tags with href starting with /job-offer/
        # We look for containers that look like offer cards
        offer_links = soup.find_all('a', href=lambda x: x and '/job-offer/' in x)

        for link in offer_links:
            try:
                # 1. Title (H3)
                title_tag = link.find('h3')
                # Fallback: sometimes it's H2 or just text in a specific class
                if not title_tag:
                     title_tag = link.find('h2')
                
                title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"

                # 2. URL and Slug
                href = link.get('href')
                full_url = f"https://justjoin.it{href}"
                slug = href.split('/')[-1]

                # 3. Company
                # Try to extract from URL slug first (reliable)
                # Slug format: company-name--job-title-...
                # But it varies. Let's try to find it in the card.
                # In MUI structure, company is often a text block.
                # A heuristic: looking for text that isn't title, isn't salary, isn't location.
                
                # Let's rely on slug for company distinctness if parsing fails, 
                # but typically there is a company name element.
                # Without exact class, we can try to guess or leave as "Unknown" 
                # (Dedup works on Title+Company+Tags, so "Unknown" isn't ideal).
                
                # Attempt to retrieve company from text content if we can identify it
                # For now, let's try to parse formatting from slug if possible, 
                # or finding the element following the title?
                company = "Unknown"
                if "--" in slug:
                    # simplistic extraction
                    parts = slug.split("--")
                    if len(parts) > 0:
                        company = parts[0].replace("-", " ").title()

                # 4. Tags
                # Look for pills/chips. Usually short text strings in divs/spans
                # We can collect text from children that are not Title/Company/Salary
                tags = []
                # Simple extraction of text nodes that look like tags (e.g. valid skills)
                # This is hard without specific classes.
                # Let's rely on the strategy: we need title/link mostly.
                
                offers.append({
                    'title': title,
                    'company': company,
                    'salary': "Undisclosed", # Hard to parse without class
                    'location': "Krakow", # We scraped Krakow page
                    'tags': "", # Placeholder
                    'link_slug': slug,
                    'full_url': full_url
                })

            except Exception as e:
                print(f"Error parsing JustJoin offer: {e}")
                continue

        return offers

    def run(self, url, save_dir="data"):
        html = self.fetch(url)
        return self.parse(html)
