import re
import os
from bs4 import BeautifulSoup
from .base import ScrapingStrategy
from utils.converter import html_to_markdown, sanitize_filename

class NoFluffJobsStrategy(ScrapingStrategy):
    def fetch(self, url):
        print(f"Fetching {url}")
        self.driver.get(url)
        # Scroll down is often needed for infinite scroll, 
        # but for now let's stick to what's loaded or maybe basic scroll?
        # JustJoin strategy didn't have explicit scroll, assuming simple page load.
        return self.driver.page_source

    def parse(self, soup):
        offers = []

        # Find all job posting items
        # Based on user snippet: <a class="posting-list-item ...">
        postings = soup.find_all("a", class_=lambda x: x and "posting-list-item" in x)
        
        for post in postings:
            try:
                # Link
                link_suffix = post.get('href')
                if not link_suffix: continue
                full_url = f"https://nofluffjobs.com{link_suffix}"
                # Slug is the last part
                slug = link_suffix.split('/')[-1]
                
                # Title
                # <h3 class="posting-title__position ..."> Title </h3>
                title_tag = post.find("h3", class_="posting-title__position")
                title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"
                # Remove "NEW" badge text if caught
                title = title.replace("NEW", "").strip()

                # Company
                # <h4 class="company-name ..."> Company </h4>
                company_tag = post.find("h4", class_="company-name")
                company = company_tag.get_text(strip=True) if company_tag else "Unknown"

                # Tags
                # <nfj-posting-item-tiles> ... <span class="posting-tag ..."> Tag </span>
                tags = []
                tiles_section = post.find("nfj-posting-item-tiles")
                if tiles_section:
                    tag_spans = tiles_section.find_all("span", class_="posting-tag")
                    for span in tag_spans:
                        tags.append(span.get_text(strip=True))
                
                tags_str = ", ".join(tags[:5])
                
                offers.append({
                    'title': title,
                    'company': company,
                    'tags': tags_str,
                    'link_slug': slug,
                    'full_url': full_url
                })
                
            except Exception as e:
                print(f"Error parsing offer element: {e}")
                continue
                
        return offers

    def run(self, url, save_dir="data"):
        html = self.fetch(url)
        
        # Parse HTML directly
        soup = BeautifulSoup(html, 'html.parser')
        
        # Fallback print for debugging
        # print(soup.prettify()[:1000])
        
        offers = self.parse(soup)
        return offers
