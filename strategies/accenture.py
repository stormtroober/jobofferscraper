import time
from bs4 import BeautifulSoup
from .base import ScrapingStrategy
from selenium.webdriver.common.by import By

class AccentureStrategy(ScrapingStrategy):
    def fetch(self, url):
        self.driver.get(url)
        time.sleep(5)  # Wait for page to load
        
        # Accept cookies if the banner appears
        try:
            btn = self.driver.find_element(By.ID, "onetrust-accept-btn-handler")
            if btn:
                self.driver.execute_script("arguments[0].click();", btn)
                time.sleep(2)
        except:
            pass

        # Expand cards to get the direct links loaded into the DOM
        try:
            expand_buttons = self.driver.find_elements(By.CSS_SELECTOR, "div.rad-filters-vertical__job-card button")
            for btn in expand_buttons:
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView(); arguments[0].click();", btn)
                except:
                    pass
            time.sleep(3)  # Wait for animations and DOM inserts
        except Exception as e:
            print(f"Error expanding Accenture cards: {e}")

        return self.driver.page_source

    def parse(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        offers = []

        cards = soup.select('div.rad-filters-vertical__job-card')
        seen_urls = set()

        for card in cards:
            try:
                title_tag = card.select_one('h3')
                if not title_tag:
                    continue
                title = title_tag.get_text(strip=True)
                
                link_tag = card.select_one('a.rad-filters-vertical__job-card-content-link-button')
                if not link_tag or not link_tag.get('href'):
                    continue
                    
                href = link_tag.get('href')
                full_url = f"https://www.accenture.com{href}" if href.startswith('/') else href
                
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)
                
                slug = full_url.split('id=')[-1].split('&')[0] if 'id=' in full_url else full_url.split('/')[-1]

                company = "Accenture"
                salary = "Undisclosed"
                
                loc_tag = card.select_one('.rad-filters-vertical__job-card-location')
                location = loc_tag.get_text(strip=True) if loc_tag else "Unknown"

                tags_elements = card.select('ul.rad-filters-vertical__job-card-meta-list li')
                tags_list = [t.get_text(strip=True) for t in tags_elements]
                tags_str = ", ".join(tags_list) if tags_list else ""

                offers.append({
                    'title': title,
                    'company': company,
                    'salary': salary,
                    'location': location,
                    'tags': tags_str,
                    'link_slug': slug,
                    'full_url': full_url
                })

            except Exception as e:
                print(f"Error parsing Accenture offer: {e}")
                continue

        return offers

    def run(self, url, save_dir="data"):
        html = self.fetch(url)
        return self.parse(html)
