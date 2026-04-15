"""Deep scraping strategy for careers.reversegroup.io – TODO: implement."""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from strategies.base_deep import DeepScrapingStrategy


class ReverseGroupDeepStrategy(DeepScrapingStrategy):
    _JD_SELECTOR = ""  # TODO: inspect the page and fill this in

    def extract(self, url: str) -> str:
        print(f"  [ReverseGroupDeepStrategy] Extracting JD from {url}")
        self.driver.get(url)

        wait = WebDriverWait(self.driver, 15)

        # TODO: replace with real selector once inspected
        raise NotImplementedError(
            "ReverseGroupDeepStrategy.extract() not yet implemented. "
            "Inspect the job page and fill in _JD_SELECTOR."
        )
