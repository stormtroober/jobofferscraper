import time
import re
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .base import ScrapingStrategy

BASE_URL = "https://www.capgemini.com"


class CapgeminiStrategy(ScrapingStrategy):
    def fetch(self, url):
        self.driver.get(url)
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "li.JobRow-module__job-card-wrapper___PZJMh"))
        )
        time.sleep(2)
        return self.driver.page_source

    def parse(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        offers = []

        for card in soup.select("li.JobRow-module__job-card-wrapper___PZJMh"):
            try:
                link_tag = card.select_one("a.JobRow-module__job-card___riAUE")
                if not link_tag:
                    continue

                href = link_tag.get("href", "")
                full_url = f"{BASE_URL}{href}" if href.startswith("/") else href
                if not full_url:
                    continue

                title_tag = card.select_one("div.JobRow-module__title___dsFeR")
                title = title_tag.get_text(strip=True) if title_tag else "Unknown"

                tags_els = card.select("ul.JobRow-module__features___dmI2i li")
                tags_str = ", ".join(el.get_text(strip=True) for el in tags_els)

                offers.append({
                    "title": title,
                    "company": "Capgemini",
                    "salary": "Undisclosed",
                    "location": "Kraków",
                    "tags": tags_str,
                    "link_slug": href.split("/")[-1] if "/" in href else href,
                    "full_url": full_url,
                })
            except Exception as e:
                print(f"Error parsing Capgemini offer: {e}")

        return offers

    def _get_total_pages(self):
        """Return number of pages from pagination buttons."""
        try:
            btns = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".Pagination-module__pagination-container___GhQ2r button"
            )
            if not btns:
                return 1
            return len(btns)
        except Exception:
            return 1

    def _go_to_page(self, page_number):
        """Click the pagination button for the given 1-based page number."""
        try:
            btns = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".Pagination-module__pagination-container___GhQ2r button"
            )
            target = btns[page_number - 1]
            self.driver.execute_script("arguments[0].click();", target)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.JobRow-module__job-card-wrapper___PZJMh"))
            )
            time.sleep(2)
            return True
        except Exception as e:
            print(f"Error navigating to page {page_number}: {e}")
            return False

    def run(self, url, save_dir="data"):
        self.driver.get(url)
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "li.JobRow-module__job-card-wrapper___PZJMh"))
        )
        time.sleep(2)

        total_pages = self._get_total_pages()
        print(f"  [CapgeminiStrategy] {total_pages} page(s) found")

        all_offers = []
        seen_urls = set()

        for page in range(1, total_pages + 1):
            if page > 1:
                if not self._go_to_page(page):
                    break

            html = self.driver.page_source
            offers = self.parse(html)

            for offer in offers:
                if offer["full_url"] not in seen_urls:
                    seen_urls.add(offer["full_url"])
                    all_offers.append(offer)

            print(f"  [CapgeminiStrategy] page {page}/{total_pages}: {len(offers)} offers")

        return all_offers
