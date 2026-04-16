import time
from bs4 import BeautifulSoup
from .base import ScrapingStrategy

BASE_URL = "https://mycareer.hsbc.com"

class HSBCStrategy(ScrapingStrategy):
    def fetch(self, url):
        self.driver.get(url)
        time.sleep(6)  # JS-rendered ATS
        return self.driver.page_source

    def parse(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        offers = []
        seen_urls = set()

        cards = soup.select('article.article--result')

        for card in cards:
            try:
                a_tag = card.select_one('h3 a')
                if not a_tag:
                    continue

                title = a_tag.get_text(strip=True)
                href = a_tag.get('href', '')
                full_url = f"{BASE_URL}{href}" if href.startswith('/') else href

                if not full_url or full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                slug = full_url.rstrip('/').split('/')[-1]

                location_tag = card.select_one('span.location')
                location = location_tag.get_text(strip=True) if location_tag else 'Unknown'

                tag_items = card.select('div.article__header__text__subtitle .item__container span.article--item:not(.item--location)')
                tags = ', '.join(' '.join(t.get_text().split()) for t in tag_items if t.get_text(strip=True))

                offers.append({
                    'title': title,
                    'company': 'HSBC',
                    'salary': 'Undisclosed',
                    'location': location,
                    'tags': tags,
                    'link_slug': slug,
                    'full_url': full_url
                })

            except Exception as e:
                print(f"Error parsing HSBC offer: {e}")
                continue

        return offers

    def run(self, url, save_dir="data"):
        html = self.fetch(url)
        return self.parse(html)
