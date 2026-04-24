import time
from bs4 import BeautifulSoup
from .base import ScrapingStrategy

BASE_URL = "https://join.ventionteams.com"

class VentionStrategy(ScrapingStrategy):
    def fetch(self, url):
        self.driver.get(url)
        time.sleep(5)
        return self.driver.page_source

    def parse(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        offers = []
        seen_urls = set()

        # Job cards are <a href="/job-openings/{slug}"> containing two spans:
        # first span = title, second span = location
        for a_tag in soup.find_all('a', href=lambda h: h and h.startswith('/job-openings/')):
            href = a_tag.get('href', '')
            full_url = f"{BASE_URL}{href}"

            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            spans = a_tag.find_all('span')
            title = spans[0].get_text(strip=True) if len(spans) > 0 else ''
            location = spans[1].get_text(strip=True) if len(spans) > 1 else 'Unknown'

            if not title:
                continue

            slug = href.split('/')[-1]

            offers.append({
                'title': title,
                'company': 'Vention',
                'salary': 'Undisclosed',
                'location': location,
                'tags': '',
                'link_slug': slug,
                'full_url': full_url,
            })

        return offers

    def run(self, url, save_dir="data"):
        html = self.fetch(url)
        return self.parse(html)
