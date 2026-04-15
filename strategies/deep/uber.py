"""Deep scraping strategy for uber.com careers – TODO: implement."""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from strategies.base_deep import DeepScrapingStrategy


class UberDeepStrategy(DeepScrapingStrategy):
    _JD_SELECTOR = "[data-testid='job-description']"  # TODO: verify

    def extract(self, url: str) -> str:
        print(f"  [UberDeepStrategy] Extracting JD from {url}")
        self.driver.get(url)

        wait = WebDriverWait(self.driver, 15)
        element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, self._JD_SELECTOR))
        )
        self.driver.execute_script("arguments[0].scrollIntoView();", element)
        time.sleep(1)

        return self.cleanup(element.text)
