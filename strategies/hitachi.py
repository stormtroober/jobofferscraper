import re
import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base import ScrapingStrategy

BASE_URL = "https://careers.hitachi.com"
MAX_PAGES = 10
CHALLENGE_RETRIES = 6


class HitachiStrategy(ScrapingStrategy):
    """Strategy for careers.hitachi.com (Phenom People platform).

    The site is protected by Cloudflare (plain HTTP requests get 403), so a
    real browser is required. Results are server-side rendered: the offers
    for the category requested in the URL live inside
    div.jobs-section__list > div.jobs-section__item and nothing else is
    parsed, so only offers of that category are extracted.
    """

    def _page_url(self, url, page):
        if page <= 1:
            return url
        sep = "&" if "?" in url else "?"
        return f"{url}{sep}page={page}"

    def fetch(self, url):
        # Cloudflare intermittently serves a "Just a moment..." challenge to
        # headless browsers; retrying usually gets through.
        for attempt in range(1, CHALLENGE_RETRIES + 1):
            self.driver.get(url)
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "div.jobs-section__inner")
                    )
                )
                return self.driver.page_source
            except Exception:
                print(f"[HitachiStrategy] attempt {attempt}/{CHALLENGE_RETRIES} blocked (title: {self.driver.title!r}), retrying")
                time.sleep(3)

        print("[HitachiStrategy] jobs-section not found after all attempts")
        return self.driver.page_source

    @staticmethod
    def _clean_text(el):
        for span in el.find_all("span", class_=lambda c: c and "hide" in c):
            span.decompose()
        return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()

    def parse(self, html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        offers = []

        items = soup.select("div.jobs-section__list div.jobs-section__item")
        if not items:
            if not soup.select("div.jobs-section__inner"):
                print("[HitachiStrategy] jobs-section missing (likely blocked by Cloudflare)")
            return []

        for el in items:
            try:
                link_tag = el.find("a", href=lambda h: h and "/jobs/" in h)
                if not link_tag:
                    continue

                full_url = link_tag["href"].split("?")[0]
                if full_url.startswith("/"):
                    full_url = f"{BASE_URL}{full_url}"
                title = link_tag.get_text(strip=True)

                location, company = "Unknown", "Unknown"
                for col in el.select("div.columns"):
                    label_span = col.find("span", class_=lambda c: c and "hide" in c)
                    label = label_span.get_text(strip=True).rstrip(":").lower() if label_span else ""
                    text = self._clean_text(col)
                    if not text:
                        continue
                    if label == "location" or (not label and "large-4" in col.get("class", [])):
                        location = text
                    elif label == "company" or (not label and "large-3" in col.get("class", [])):
                        company = text

                offers.append({
                    'title': title,
                    'company': company,
                    'tags': location,
                    'link_slug': full_url.split("/")[-1],
                    'full_url': full_url,
                })

            except Exception as e:
                print(f"[HitachiStrategy] Error parsing offer: {e}")
                continue

        return offers

    def run(self, url, save_dir="data"):
        offers = []
        seen = set()

        for page in range(1, MAX_PAGES + 1):
            html = self.fetch(self._page_url(url, page))
            page_offers = self.parse(html)

            new = [o for o in page_offers if o['full_url'] not in seen]
            if not new:
                break

            for o in new:
                seen.add(o['full_url'])
                offers.append(o)

        return offers
