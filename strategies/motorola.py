import time
from bs4 import BeautifulSoup
from .base import ScrapingStrategy

BASE_URL = "https://motorolasolutions.wd5.myworkdayjobs.com"

class MotorolaStrategy(ScrapingStrategy):
    def fetch(self, url):
        self.driver.get(url)
        time.sleep(8)  # Workday is slow to render
        return self.driver.page_source

    def parse(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        offers = []
        seen_urls = set()

        # Workday uses data-automation-id attributes which are stable across portals
        cards = soup.find_all('li', class_='css-1q2dra3')

        for card in cards:
            try:
                # Title + Link
                a_tag = card.find('a', attrs={'data-automation-id': 'jobTitle'})
                if not a_tag:
                    continue

                title = a_tag.get_text(strip=True)
                href = a_tag.get('href', '')

                # Strip tracking query params — keep only the job path + id
                job_path = href.split('?')[0]
                full_url = f"{BASE_URL}{job_path}" if job_path.startswith('/') else job_path

                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)

                # Job ID from href (e.g. "_R59564" at end of path)
                slug = job_path.split('_')[-1] if '_' in job_path else job_path.split('/')[-1]

                # Location
                loc_div = card.find('div', attrs={'data-automation-id': 'locations'})
                location = "Unknown"
                if loc_div:
                    loc_texts = [s.get_text(strip=True) for s in loc_div.find_all('dd')]
                    if not loc_texts:
                        # Fallback: grab all text, strip icon text
                        location = loc_div.get_text(separator=' ', strip=True)
                        # Clean up SVG artifacts
                        if len(location) > 80:
                            location = "Krakow, Poland"
                    else:
                        location = ", ".join(loc_texts)

                # Posted date / any tags visible in meta
                tags_parts = []
                meta_div = card.find('div', class_='css-1y87fhn')
                if meta_div:
                    for dl in meta_div.find_all('dl'):
                        label = dl.find('dt')
                        value = dl.find('dd')
                        if label and value:
                            label_text = label.get_text(strip=True).lower()
                            if 'location' not in label_text:
                                tags_parts.append(value.get_text(strip=True))

                offers.append({
                    'title': title,
                    'company': 'Motorola Solutions',
                    'salary': 'Undisclosed',
                    'location': location,
                    'tags': ', '.join(tags_parts),
                    'link_slug': slug,
                    'full_url': full_url
                })

            except Exception as e:
                print(f"Error parsing Motorola card: {e}")
                continue

        return offers

    def run(self, url, save_dir="data"):
        html = self.fetch(url)
        return self.parse(html)
