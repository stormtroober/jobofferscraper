import json
import re

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .base import ScrapingStrategy


BASE_URL = "https://www.pepsicojobs.com"


class PepsiCoStrategy(ScrapingStrategy):
    """Scraper for the PepsiCo careers site (Jibe platform)."""

    def fetch(self, url):
        self.driver.get(url)
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "a[href*='/main/jobs/'], [type='application/ld+json']")
                )
            )
        except Exception:
            print("[PepsiCoStrategy] job results not found after wait")
        return self.driver.page_source

    @staticmethod
    def _text(element):
        return re.sub(r"\s+", " ", element.get_text(" ", strip=True)).strip()

    def parse(self, html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        offers = []
        seen = set()

        # Jibe can expose the same results as JSON-LD or rendered job links.
        for script in soup.select("script[type='application/ld+json']"):
            try:
                data = json.loads(script.string or script.get_text())
            except (json.JSONDecodeError, TypeError):
                continue
            entries = data if isinstance(data, list) else [data]
            for entry in entries:
                if entry.get("@type") != "JobPosting" or not entry.get("url"):
                    continue
                self._add_offer(offers, seen, entry["url"], entry.get("title"),
                                entry.get("hiringOrganization", {}).get("name", "Unknown"),
                                entry.get("jobLocation", ""))

        for link in soup.select("a[href*='/main/jobs/']"):
            href = link.get("href", "").split("?")[0]
            if href.rstrip("/") == f"{BASE_URL}/main/jobs":
                continue
            card = link.find_parent(["li", "article", "div"])
            title = self._text(link)
            company = "PepsiCo"
            tags = ""
            if card:
                title_node = card.select_one("[class*='title'], [class*='job-title'], h2, h3")
                title = self._text(title_node) if title_node else title
                location_node = card.select_one("[class*='location'], [class*='Location']")
                tags = self._text(location_node) if location_node else ""
            self._add_offer(offers, seen, href, title, company, tags)

        return offers

    @staticmethod
    def _add_offer(offers, seen, href, title, company, tags):
        full_url = href if href.startswith("http") else f"{BASE_URL}{href}"
        if full_url in seen or not title:
            return
        seen.add(full_url)
        offers.append({
            "title": title,
            "company": company or "PepsiCo",
            "tags": tags if isinstance(tags, str) else "",
            "link_slug": full_url.rstrip("/").split("/")[-1],
            "full_url": full_url,
        })

    def run(self, url, save_dir="data"):
        return self.parse(self.fetch(url))
