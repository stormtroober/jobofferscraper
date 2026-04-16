import time
from bs4 import BeautifulSoup
from .base import ScrapingStrategy

BASE_URL = "https://careers.epam.com"

class EPAMStrategy(ScrapingStrategy):
    def fetch(self, url):
        self.driver.get(url)
        time.sleep(7)  # JS-rendered Angular app
        return self.driver.page_source

    def parse(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        offers = []
        seen_urls = set()

        # Anchors identified via live DOM inspection (data-testid stable across CSS module hash changes)
        anchors = soup.select('a[data-testid="job-card-link"]')

        for a_tag in anchors:
            try:
                href = a_tag.get('href', '')
                full_url = f"{BASE_URL}{href}" if href.startswith('/') else href

                if not full_url or full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                slug = href.rstrip('/').split('/')[-1]

                title_tag = a_tag.select_one('span[data-testid="job-card-title"]')
                title = title_tag.get_text(strip=True) if title_tag else a_tag.get_text(strip=True)

                # Walk up to card container to find location/tags siblings
                card = a_tag.find_parent(attrs={'class': lambda c: c and any('JobCard_accordionHeader' in cls for cls in c)})
                if not card:
                    card = a_tag

                location_tag = card.select_one('[class*="JobCard_workplaceWithLocation"]')
                location = location_tag.get_text(strip=True) if location_tag else 'Poland'

                tags_tag = card.select_one('[class*="JobCard_extraInfo"]')
                # extraInfo contains location too — grab all text minus location
                tags = ''
                if tags_tag:
                    loc_text = location_tag.get_text(strip=True) if location_tag else ''
                    full_text = tags_tag.get_text(' | ', strip=True)
                    tags = full_text.replace(loc_text, '').strip(' |')

                offers.append({
                    'title': title,
                    'company': 'EPAM',
                    'salary': 'Undisclosed',
                    'location': location,
                    'tags': tags,
                    'link_slug': slug,
                    'full_url': full_url
                })

            except Exception as e:
                print(f"Error parsing EPAM offer: {e}")
                continue

        return offers

    def run(self, url, save_dir="data"):
        html = self.fetch(url)
        return self.parse(html)
