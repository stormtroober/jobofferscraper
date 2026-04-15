"""
Generic / fallback deep scraping strategy.

Used whenever no site-specific strategy has been implemented yet.
Tries a ranked list of heuristic CSS selectors and falls back to the
full <body> text if nothing meaningful is found.
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from strategies.base_deep import DeepScrapingStrategy


# Ordered list of selectors to probe, from most specific to most generic
_CANDIDATE_SELECTORS = [
    "main",
    "article",
    "[class*='job-description']",
    "[class*='offer-content']",
    "[class*='job-details']",
    "[id*='description']",
    "[id*='job']",
]

_MIN_MEANINGFUL_LENGTH = 200


class GenericDeepStrategy(DeepScrapingStrategy):
    """
    Heuristic fallback: tries a list of common selectors and picks the
    candidate with the most text.  Falls back to the whole <body> if
    nothing useful is found.
    """

    def extract(self, url: str) -> str:
        print(f"  [GenericDeepStrategy] Nessuna strategia specifica – fallback generico per {url}")
        self.driver.get(url)

        wait = WebDriverWait(self.driver, 15)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)

        best_text = ""
        for selector in _CANDIDATE_SELECTORS:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                if el.is_displayed():
                    txt = el.text.strip()
                    if len(txt) > len(best_text):
                        best_text = txt

        if len(best_text) < _MIN_MEANINGFUL_LENGTH:
            best_text = self.driver.find_element(By.TAG_NAME, "body").text

        return self.cleanup(best_text)
