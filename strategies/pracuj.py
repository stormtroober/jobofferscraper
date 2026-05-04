import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base import ScrapingStrategy

BASE_URL = "https://www.pracuj.pl"


class PracujStrategy(ScrapingStrategy):
    def fetch(self, url):
        self.driver.get(url)

        # Dismiss cookie consent if present
        try:
            btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-test='button-submitCookie']"))
            )
            btn.click()
            time.sleep(1)
        except Exception:
            pass

        # Wait for offers list
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#offers-list"))
            )
        except Exception:
            print("[PracujStrategy] #offers-list not found after wait")

        return self.driver.page_source

    def parse(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        offers = []

        container = soup.find(id="offers-list")
        if not container:
            print("[PracujStrategy] Could not find #offers-list")
            return []

        # Each offer card
        offer_elements = container.select("div[data-test='default-offer']")
        if not offer_elements:
            # fallback: try article tags
            offer_elements = container.find_all("article")

        for el in offer_elements:
            try:
                # Link + title
                link_tag = el.select_one("a[data-test='link-offer']")
                if not link_tag:
                    link_tag = el.find("a", href=True)
                if not link_tag:
                    continue

                href = link_tag.get("href", "")
                full_url = href if href.startswith("http") else f"{BASE_URL}{href}"
                # Strip tracking params
                full_url = full_url.split("?")[0]

                title_el = el.select_one("[data-test='offer-title']")
                if not title_el:
                    title_el = link_tag
                title = title_el.get_text(strip=True) if title_el else "Unknown"

                # Company
                company_el = el.select_one("[data-test='text-company-name']")
                company = company_el.get_text(strip=True) if company_el else "Unknown"

                # Tags: technologies / requirements listed
                tag_els = el.select("[data-test='technologies-item']")
                if not tag_els:
                    tag_els = el.select("[data-test='offer-tags'] li")
                tags = ", ".join(t.get_text(strip=True) for t in tag_els[:6])

                offers.append({
                    'title': title,
                    'company': company,
                    'tags': tags,
                    'link_slug': full_url.split("/")[-1],
                    'full_url': full_url,
                })

            except Exception as e:
                print(f"[PracujStrategy] Error parsing offer: {e}")
                continue

        return offers

    def run(self, url, save_dir="data"):
        html = self.fetch(url)
        return self.parse(html)
