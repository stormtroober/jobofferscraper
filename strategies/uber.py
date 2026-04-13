import time
from bs4 import BeautifulSoup
from .base import ScrapingStrategy

class UberStrategy(ScrapingStrategy):
    def fetch(self, url):
        self.driver.get(url)
        time.sleep(5)  # Wait for React to render
        return self.driver.page_source

    def parse(self, html_content, url=""):
        soup = BeautifulSoup(html_content, 'html.parser')
        offers = []

        # Find all job links
        offer_links = soup.find_all('a', href=lambda x: x and '/careers/list/' in x)
        
        seen_urls = set()

        for link in offer_links:
            try:
                href = link.get('href')
                
                # Exclude navigation links that also contain '/careers/list/'
                if href.endswith('/careers/list/') or '?' in href:
                    continue
                
                title = link.get_text(strip=True)
                if not title:
                    continue
                
                full_url = f"https://www.uber.com{href}" if href.startswith('/') else href
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)
                
                slug = href.split('/')[-1]

                company = "Uber"
                
                # Extract location from URL if possible
                location = "Krakow" 
                if "location=" in url:
                    loc_param = url.split("location=")[1].split("&")[0]
                    if "--" in loc_param:
                        location = loc_param.split("--")[-1].replace("%20", " ")
                    else:
                        location = loc_param.replace("%20", " ")

                salary = "Undisclosed"
                tags = ""

                offers.append({
                    'title': title,
                    'company': company,
                    'salary': salary,
                    'location': location,
                    'tags': tags,
                    'link_slug': slug,
                    'full_url': full_url
                })

            except Exception as e:
                print(f"Error parsing Uber offer: {e}")
                continue

        return offers

    def run(self, url, save_dir="data"):
        html = self.fetch(url)
        return self.parse(html, url)
