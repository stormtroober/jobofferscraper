"""
Deep scraping strategy – stub template.

Copy this file, rename the class and MODULE_SITE constant, then implement
the extract() method for the target site.

Steps to add a new strategy:
  1. cp strategies/deep/_stub_template.py strategies/deep/<site>.py
  2. Rename the class to <Site>DeepStrategy
  3. Implement extract(): navigate, wait, locate the JD element, return text
  4. Register the import in strategies/deep_factory.py
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from strategies.base_deep import DeepScrapingStrategy

MODULE_SITE = "example.com"  # change this


class ExampleDeepStrategy(DeepScrapingStrategy):
    """TODO: implement for MODULE_SITE."""

    # CSS selector (or XPath) that wraps the job description block
    _JD_SELECTOR = ""  # TODO: fill in

    def extract(self, url: str) -> str:
        print(f"  [{self.__class__.__name__}] Extracting JD from {url}")
        self.driver.get(url)

        wait = WebDriverWait(self.driver, 15)

        # TODO: replace with the real selector / wait condition
        element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, self._JD_SELECTOR))
        )
        self.driver.execute_script("arguments[0].scrollIntoView();", element)
        time.sleep(1)

        return self.cleanup(element.text)
