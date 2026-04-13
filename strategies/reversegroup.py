import time
from bs4 import BeautifulSoup
from .base import ScrapingStrategy

class ReverseGroupStrategy(ScrapingStrategy):
    def fetch(self, url):
        self.driver.get(url)
        time.sleep(3)  # Wait for page to render
        return self.driver.page_source

    def parse(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        offers = []

        jobs_list = soup.find('ul', id='jobs_list_container')
        if not jobs_list:
            return offers

        seen_urls = set()

        for li in jobs_list.find_all('li', class_='w-full'):
            try:
                a_tag = li.find('a')
                if not a_tag:
                    continue
                
                href = a_tag.get('href')
                title = a_tag.get_text(strip=True)
                
                full_url = f"https://careers.reversegroup.io{href}" if href.startswith('/') else href
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)
                
                slug = full_url.split('/')[-1]

                company = "Reverse Tech"
                salary = "Undisclosed"
                location = "Unknown"
                tags = []

                # Find the container for department, location, etc.
                meta_div = li.find('div', class_=lambda x: x and 'mt-1' in x and 'text-md' in x)
                if meta_div:
                    # Some spans are direct children, others might be nested (like the wifi icon one)
                    # Let's extract all text from spans, excluding empty ones or just dots
                    spans = meta_div.find_all('span', recursive=False)
                    meta_texts = [s.get_text(strip=True) for s in spans if s.get_text(strip=True) and s.get_text(strip=True) != '·']
                    
                    if len(meta_texts) > 0:
                        tags.append(meta_texts[0]) # Usually department
                    if len(meta_texts) > 1:
                        location = meta_texts[1] # Usually location
                    if len(meta_texts) > 2:
                        tags.append(meta_texts[2]) # Usually remote status

                offers.append({
                    'title': title,
                    'company': company,
                    'salary': salary,
                    'location': location,
                    'tags': ", ".join(tags) if tags else "",
                    'link_slug': slug,
                    'full_url': full_url
                })
            except Exception as e:
                print(f"Error parsing ReverseGroup offer: {e}")
                continue

        return offers

    def run(self, url, save_dir="data"):
        html = self.fetch(url)
        return self.parse(html)
