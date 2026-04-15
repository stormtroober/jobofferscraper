import time
from bs4 import BeautifulSoup
from .base import ScrapingStrategy

BASE_URL = "https://careers.cognizant.com"

class CognizantStrategy(ScrapingStrategy):
    def fetch(self, url):
        self.driver.get(url)
        time.sleep(8)  # JS-rendered via Phenom People ATS
        return self.driver.page_source

    def parse(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        offers = []
        seen_urls = set()

        cards = soup.select('div.card.card-job')

        for card in cards:
            try:
                a_tag = card.select_one('h2.card-title a.stretched-link')
                if not a_tag:
                    continue

                title = a_tag.get_text(strip=True)
                href = a_tag.get('href', '')
                full_url = f"{BASE_URL}{href}" if href.startswith('/') else href

                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                job_id = card.get('data-id', '')
                slug = job_id if job_id else href.split('/')[-2]

                meta_items = [li.get_text(strip=True) for li in card.select('ul.list-inline.job-meta li.list-inline-item')]
                location = meta_items[0] if meta_items else 'Unknown'
                tags = meta_items[1] if len(meta_items) > 1 else ''

                offers.append({
                    'title': title,
                    'company': 'Cognizant',
                    'salary': 'Undisclosed',
                    'location': location,
                    'tags': tags,
                    'link_slug': slug,
                    'full_url': full_url
                })

            except Exception as e:
                print(f"Error parsing Cognizant offer: {e}")
                continue

        return offers

    def run(self, url, save_dir="data"):
        html = self.fetch(url)
        return self.parse(html)
