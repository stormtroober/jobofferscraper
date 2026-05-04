import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from strategies.base_deep import DeepScrapingStrategy


class PracujDeepStrategy(DeepScrapingStrategy):
    _JD_SELECTOR = "div[data-test='section-job-description']"

    def extract(self, url: str) -> str:
        print(f"  [PracujDeepStrategy] Extracting JD from {url}")
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

        wait = WebDriverWait(self.driver, 15)
        try:
            element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self._JD_SELECTOR))
            )
        except Exception:
            # fallback to generic content area
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, "div[data-test='offer-description']")
            except Exception:
                return ""

        self.driver.execute_script("arguments[0].scrollIntoView();", element)
        time.sleep(1)

        return self.cleanup(element.text)
