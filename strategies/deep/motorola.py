"""Deep scraping strategy for motorolasolutions.wd5.myworkdayjobs.com – TODO: implement."""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from strategies.base_deep import DeepScrapingStrategy


class MotorolaDeepStrategy(DeepScrapingStrategy):
    _JD_SELECTOR = ""  # TODO: inspect the Workday page and fill this in

    def extract(self, url: str) -> str:
        print(f"  [MotorolaDeepStrategy] Extracting JD from {url}")
        self.driver.get(url)

        wait = WebDriverWait(self.driver, 15)

        # TODO: replace with real selector once inspected
        raise NotImplementedError(
            "MotorolaDeepStrategy.extract() not yet implemented. "
            "Inspect the Workday job page and fill in _JD_SELECTOR."
        )
