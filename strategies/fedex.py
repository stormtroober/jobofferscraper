from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .base import ScrapingStrategy


BASE_URL = "https://careers.fedex.com"
MAX_PAGES = 100


class FedExStrategy(ScrapingStrategy):
    """Strategy for FedEx career searches, including the path-based pager."""

    def fetch(self, url):
        self.driver.get(url)
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "li[data-testid='jobs-list-only_jobs-list_item']")
                )
            )
        except Exception:
            print("[FedExStrategy] job results not found after wait")
        return self.driver.page_source

    @staticmethod
    def _text(element):
        return " ".join(element.get_text(" ", strip=True).split())

    def parse(self, html_content):
        soup = BeautifulSoup(html_content, "html.parser")
        offers = []

        for card in soup.select("li[data-testid='jobs-list-only_jobs-list_item']"):
            link = card.select_one(".results-list__item-title--link[href]")
            if not link:
                continue

            href = urljoin(BASE_URL, link["href"].split("?")[0])
            title = self._text(link)
            company_el = card.select_one(".results-list__item-brand--label")
            location_el = card.select_one(".results-list__item-street--label")

            offers.append({
                "title": title,
                "company": self._text(company_el) if company_el else "FedEx",
                "tags": self._text(location_el) if location_el else "",
                "link_slug": href.rstrip("/").split("/")[-1],
                "full_url": href,
            })

        return offers

    @staticmethod
    def _next_url(current_url, soup):
        next_link = soup.select_one("a[data-testid='jobs-pagination_link_next']")
        if not next_link or next_link.get("aria-disabled") == "true":
            return None

        href = next_link.get("href")
        if not href:
            return None

        next_url = urljoin(current_url, href)
        current = urlsplit(current_url)
        target = urlsplit(next_url)
        if target.query:
            return next_url

        # FedEx's pager can omit the search query from the path-based next link.
        # Keep all filters, while letting the path identify the next page.
        query = [(key, value) for key, value in parse_qsl(current.query, keep_blank_values=True)
                 if key != "page_number"]
        return urlunsplit((target.scheme, target.netloc, target.path, urlencode(query), target.fragment))

    def run(self, url, save_dir="data"):
        offers = []
        seen_offers = set()
        seen_pages = set()
        current_url = url

        for _ in range(MAX_PAGES):
            if current_url in seen_pages:
                break
            seen_pages.add(current_url)

            html = self.fetch(current_url)
            soup = BeautifulSoup(html, "html.parser")
            for offer in self.parse(html):
                if offer["full_url"] not in seen_offers:
                    seen_offers.add(offer["full_url"])
                    offers.append(offer)

            current_url = self._next_url(current_url, soup)
            if not current_url:
                break

        return offers
