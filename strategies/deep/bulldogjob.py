"""Deep scraping strategy for bulldogjob.com."""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from strategies.base_deep import DeepScrapingStrategy

_MIN_MEANINGFUL_LENGTH = 300

# Selectors to try in order of specificity
_JD_SELECTORS = [
    ".job-description",
    "[class*='JobDescription']",
    "[class*='job-description']",
    "[class*='job_description']",
    "[data-cy='job-description']",
    "section.description",
    "article.description",
    ".description-content",
    ".offer-description",
]

# JS fallback: find the richest visible container
_JS_FIND_RICHEST = """
return Array.from(document.querySelectorAll('div, section, article'))
  .filter(el => {
    const t = (el.innerText || '').trim();
    return t.length > 400 && el.children.length > 0;
  })
  .reduce((best, el) => {
    const rect = el.getBoundingClientRect();
    if (rect.height < 150) return best;
    const t = (el.innerText || '').trim();
    return t.length > (best ? (best.innerText || '').trim().length : 0) ? el : best;
  }, null);
"""


class BulldogJobDeepStrategy(DeepScrapingStrategy):

    def extract(self, url: str) -> str:
        print(f"  [BulldogJobDeepStrategy] Extracting JD from {url}")
        self.driver.get(url)

        wait = WebDriverWait(self.driver, 20)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)

        self._dismiss_cookies()
        time.sleep(0.5)

        # 1. Try known CSS selectors — bulldogjob renders JD in main content area
        for selector in _JD_SELECTORS:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                try:
                    txt = el.text.strip()
                    if len(txt) >= _MIN_MEANINGFUL_LENGTH:
                        print(f"  [BulldogJobDeepStrategy] Found via '{selector}', {len(txt)} chars")
                        return self.cleanup(txt)
                except Exception:
                    continue

        # 2. JS fallback: richest visible container
        el = self.driver.execute_script(_JS_FIND_RICHEST)
        if el:
            txt = self._trim_to_jd(el.text.strip())
            if len(txt) >= _MIN_MEANINGFUL_LENGTH:
                print(f"  [BulldogJobDeepStrategy] Found via JS richest-element, {len(txt)} chars")
                return self.cleanup(txt)

        # 3. Full body text as last resort
        body_text = self.driver.find_element(By.TAG_NAME, "body").text
        print(f"  [BulldogJobDeepStrategy] Falling back to body text ({len(body_text)} chars)")
        return self.cleanup(self._trim_to_jd(body_text))

    def _trim_to_jd(self, text: str) -> str:
        """Cut nav/cookie noise before the actual job content."""
        # Common section headers that mark the start of a job posting
        markers = [
            "What you will do",
            "Role and Responsibilities",
            "About the role",
            "About the job",
            "Job description",
            "Requirements",
            "Responsibilities",
            "We are looking for",
        ]
        lower = text.lower()
        for marker in markers:
            idx = lower.find(marker.lower())
            if idx != -1:
                # Also include any job title line just before the marker (up to 300 chars back)
                start = max(0, idx - 300)
                snippet = text[start:idx]
                # Find the last newline before the marker to get the surrounding block
                last_nl = snippet.rfind("\n")
                adjusted = start + last_nl + 1 if last_nl != -1 else idx
                return text[adjusted:]
        return text

    def _dismiss_cookies(self):
        selectors = [
            "button[id*='accept']",
            "button[class*='accept']",
            "button[data-testid*='accept']",
            "#onetrust-accept-btn-handler",
            "button[class*='cookie']",
            "[class*='CookieConsent'] button",
        ]
        for sel in selectors:
            for btn in self.driver.find_elements(By.CSS_SELECTOR, sel):
                try:
                    if btn.is_displayed():
                        btn.click()
                        return
                except Exception:
                    continue
